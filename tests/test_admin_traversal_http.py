"""Admin API tests for hostile paths and keep-alive framing.

The admin API is the one surface where the upstream name is fully
attacker-controlled and reaches the store with almost no normalisation
between them: `/api/fixtures?upstream=..` and
`DELETE /api/fixtures/../important` both carry it in the request target.

The store refuses those paths, but before the guard added here the
SecurityError escaped through BaseHTTPRequestHandler: a 500 whose
connection was left half-written, with a traceback on stderr. These tests
pin the status, the body, and that the connection survives.

Each entry below is the exact bytes an attacker would put on the wire and
is sent verbatim. Pre-encoding is deliberately avoided: quoting an already
percent-encoded string double-encodes it, and `%252e%252e` is a legitimate
component name, not an attack.
"""

import http.client
import json
import tempfile
import threading

import pytest

from mockrelay._05 import _06 as Config
from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import _04 as Store
from mockrelay._11 import _01 as Metrics
from mockrelay._13 import _18 as State
from mockrelay._14 import _10 as start_admin
from mockrelay.errors import ConfigError, LimitExceeded, SecurityError

TRAVERSAL = [
    "..",
    "../..",
    "..\\..",
    "....",
    "./..",
    "a/../../b",
    "a\\..\\..\\b",
    "gh/../..",
    "%2e%2e",
    "%2e%2e%2f",
    "..%2f",
    "%2e%2e%2f%2e%2e%2f",
    "..%5c..%5c",
    "/etc",
    "..%00",
    "C:%5cWindows",
]

ENCODED = [t for t in TRAVERSAL if "%" in t]


def _fx(fid, path="/users/7"):
    return _06(id=fid, upstream="u",
               match=_01(method="GET", path=path),
               request=_04(method="GET", path=path),
               response=_05(status=200, body={"ok": True}))


def _start(tmp_path, with_fixture=True):
    cfg = Config({
        "listen": "127.0.0.1:0",
        "admin_listen": "127.0.0.1:0",
        "fixtures_dir": str(tmp_path),
        "mode": "replay",
        "upstreams": {"u": {"base_url": "http://127.0.0.1:9"}},
    })
    store = Store(cfg.fixtures_dir)
    if with_fixture:
        store._06("u", _fx("good"))
    return start_admin(State(cfg, store, Metrics()))


@pytest.fixture
def admin(tmp_path):
    srv = _start(tmp_path)
    try:
        yield tmp_path, srv
    finally:
        srv.shutdown()
        srv.server_close()


def _conn(srv):
    return http.client.HTTPConnection("127.0.0.1", srv.server_address[1],
                                      timeout=5)


def _req(srv, path, method="GET", body=None, conn=None):
    own = conn is None
    c = conn or _conn(srv)
    try:
        c.request(method, path, body)
        r = c.getresponse()
        return r.status, r.read()
    finally:
        if own:
            c.close()


def _assert_tidy(status, raw, want=(400,)):
    assert status in want, (status, raw)
    text = raw.decode()
    for leak in ("Traceback", "socketserver", 'File "', "mockrelay\\_",
                 "http.server", "0x"):
        assert leak not in text, f"leaked {leak!r} in {text[:200]!r}"
    return json.loads(text)


def test_01_listing_with_a_traversal_upstream_is_a_tidy_400(admin):
    _tmp, srv = admin
    for bad in TRAVERSAL:
        status, raw = _req(srv, f"/api/fixtures?upstream={bad}")
        body = _assert_tidy(status, raw)
        assert body.get("type") == "security", (bad, body)
        assert body["error"]


def test_02_delete_with_a_traversal_upstream_is_refused(admin):
    """400 where the shape is a delete, 404 where extra segments change it.

    A payload like `a/../../b/victim` splits into more than four path
    segments, so it is not a delete route at all and never reaches the
    store. Both outcomes are acceptable; what matters is that neither is
    a 500 and neither touches a file.
    """
    _tmp, srv = admin
    for bad in TRAVERSAL:
        status, raw = _req(srv, f"/api/fixtures/{bad}/victim", method="DELETE")
        _assert_tidy(status, raw, want=(400, 404))


def test_03_delete_with_a_traversal_fixture_id_is_refused(admin):
    _tmp, srv = admin
    for bad in TRAVERSAL:
        status, raw = _req(srv, f"/api/fixtures/u/{bad}", method="DELETE")
        _assert_tidy(status, raw, want=(400, 404))


def test_04_a_literal_dot_dot_in_the_target_never_escapes(admin):
    """The unencoded form, which reaches the handler as a path segment."""
    _tmp, srv = admin
    for path in ("/api/fixtures/../important",
                 "/api/fixtures/../../important",
                 "/api/fixtures/..%5c..%5cimportant"):
        status, raw = _req(srv, path, method="DELETE")
        _assert_tidy(status, raw, want=(400, 404))


def test_05_match_probing_with_a_traversal_upstream_is_a_tidy_400(admin):
    _tmp, srv = admin
    for bad in TRAVERSAL:
        status, raw = _req(srv, f"/api/match?upstream={bad}&path=/x")
        _assert_tidy(status, raw)


def test_06_encoded_forms_are_refused_one_decode_deep(admin):
    """`%2e%2e` must not survive a single parse_qs round trip."""
    _tmp, srv = admin
    for bad in ENCODED:
        status, raw = _req(srv, f"/api/fixtures?upstream={bad}")
        _assert_tidy(status, raw)


def test_07_nothing_outside_the_fixtures_dir_was_read_or_removed(tmp_path):
    """The strongest form: put the bait outside the root and check it."""
    outside = tmp_path / "important.json"
    outside.write_text('{"secret": true}', encoding="utf-8")
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    srv = start_admin(State(
        Config({
            "listen": "127.0.0.1:0",
            "admin_listen": "127.0.0.1:0",
            "fixtures_dir": str(fixtures),
            "mode": "replay",
            "upstreams": {"u": {"base_url": "http://127.0.0.1:9"}},
        }),
        Store(fixtures), Metrics()))
    try:
        for bad in ("..", "%2e%2e", "../..", "a/../../b", "..\\.."):
            status, raw = _req(srv, f"/api/fixtures?upstream={bad}")
            _assert_tidy(status, raw)
            body = json.loads(raw)
            assert "secret" not in json.dumps(body), (bad, body)
        for bad in ("../important", "..%2fimportant", "..%5cimportant"):
            status, raw = _req(srv, f"/api/fixtures/{bad}", method="DELETE")
            _assert_tidy(status, raw, want=(400, 404))
    finally:
        srv.shutdown()
        srv.server_close()
    assert outside.exists(), "a file above the fixtures root was deleted"
    assert json.loads(outside.read_text(encoding="utf-8")) == {"secret": True}


def test_08_a_post_body_does_not_desynchronise_the_connection(admin):
    """No admin route reads a body, so it has to be drained explicitly."""
    _tmp, srv = admin
    c = _conn(srv)
    try:
        payload = json.dumps({"padding": "x" * 4096}).encode()
        status, _ = _req(srv, "/api/mode", method="POST", body=payload, conn=c)
        assert status in (200, 400, 404), status
        c.request("GET", "/api/fixtures")
        r2 = c.getresponse()
        raw = r2.read()
        assert r2.status == 200, (r2.status, raw)
        assert [f["id"] for f in json.loads(raw)] == ["good"]
    finally:
        c.close()


def test_09_a_sequence_of_traversals_leaves_the_connection_usable(admin):
    _tmp, srv = admin
    c = _conn(srv)
    try:
        for bad in ("..", "%2e%2e", "a/../../b", "..\\.."):
            c.request("GET", f"/api/fixtures?upstream={bad}")
            r = c.getresponse()
            r.read()
            assert r.status == 400, (bad, r.status)
        c.request("GET", "/api/fixtures")
        r = c.getresponse()
        raw = r.read()
        assert r.status == 200
        assert [f["id"] for f in json.loads(raw)] == ["good"]
    finally:
        c.close()


def test_10_valid_requests_still_work(admin):
    _tmp, srv = admin
    status, raw = _req(srv, "/api/fixtures?upstream=u")
    assert status == 200
    assert [f["id"] for f in json.loads(raw)] == ["good"]
    status, raw = _req(srv, "/api/match?upstream=u&path=/users/7")
    assert status == 200
    assert len(json.loads(raw)["results"]) == 1
    status, raw = _req(srv, "/api/fixtures/u/good", method="DELETE")
    assert status == 200
    assert json.loads(raw) == {"deleted": True}
    status, raw = _req(srv, "/api/fixtures/u/good", method="DELETE")
    assert status == 404


def test_11_the_dashboard_and_metrics_are_unaffected(admin):
    _tmp, srv = admin
    status, raw = _req(srv, "/")
    assert status == 200
    assert b"MockRelay" in raw
    status, raw = _req(srv, "/metrics")
    assert status == 200
    assert raw
    status, raw = _req(srv, "/api/state")
    assert status == 200
    assert json.loads(raw)["mode"] == "replay"


def test_12_concurrent_traversals_do_not_wedge_the_listener(tmp_path):
    srv = _start(tmp_path, with_fixture=False)
    results: list[int] = []
    try:
        def worker():
            for _ in range(5):
                st, _ = _req(srv, "/api/fixtures?upstream=..")
                results.append(st)

        ts = [threading.Thread(target=worker) for _ in range(4)]
        for t in ts:
            t.start()
        for t in ts:
            t.join(30)
        assert results == [400] * 20, results
    finally:
        srv.shutdown()
        srv.server_close()


class _FakeHandler:
    """Exercises the guard directly, without a socket.

    An unexpected exception raised on a server thread cannot reach the
    client, so the "does not over-catch" property has to be asserted here.
    """

    def __init__(self):
        self.sent: list[tuple[int, dict]] = []
        self.drained = False

    def _07(self, status, payload):
        self.sent.append((status, payload))

    def _15(self):
        self.drained = True


def _guarded(exc):
    """A handler method that raises `exc`, wrapped in the real guard."""
    from mockrelay._14 import _18

    def do_GET(self):
        raise exc

    return _18(do_GET)


@pytest.mark.parametrize("exc,status,kind", [
    (SecurityError("path segment '..' is not allowed"), 400, "security"),
    (LimitExceeded("too many headers"), None, "limit"),
    (ConfigError("bad yaml at line 3"), 500, "config"),
])
def test_13_the_guard_maps_each_error_kind_to_its_own_status(exc, status, kind):
    h = _FakeHandler()
    _guarded(exc)(h)
    got, body = h.sent[0]
    assert body["type"] == kind, body
    if status is not None:
        assert got == status, (got, body)
    if isinstance(exc, LimitExceeded):
        assert got == exc.status
    assert h.drained is True, "the body must be drained before dispatch"
    assert "Traceback" not in json.dumps(body)


def test_14_the_guard_does_not_swallow_an_unexpected_exception():
    """A real bug must not be dressed up as a tidy 400."""
    h = _FakeHandler()
    with pytest.raises(RuntimeError, match="genuine bug"):
        _guarded(RuntimeError("a genuine bug, not a policy decision"))(h)
    assert h.sent == []
    assert h.drained is True


def test_15_a_malformed_content_length_does_not_break_the_next_request(admin):
    """A nonsense length must not raise out of the drain."""
    _tmp, srv = admin
    c = _conn(srv)
    try:
        c.putrequest("POST", "/api/mode")
        c.putheader("Content-Length", "not-a-number")
        c.putheader("Content-Type", "application/json")
        c.endheaders()
        c.send(b"{}")
        r = c.getresponse()
        r.read()
    finally:
        c.close()
    status, raw = _req(srv, "/api/fixtures")
    assert status == 200, (status, raw)
    assert [f["id"] for f in json.loads(raw)] == ["good"]


def test_16_oversized_content_length_is_bounded(tmp_path):
    """The drain must not allocate or read without limit."""
    srv = _start(tmp_path, with_fixture=False)
    try:
        c = _conn(srv)
        try:
            c.putrequest("POST", "/api/mode")
            c.putheader("Content-Length", str(2 ** 40))
            c.putheader("Content-Type", "application/json")
            c.endheaders()
            c.send(b"{}")
            c.close()
        except OSError:
            c.close()
    finally:
        srv.shutdown()
        srv.server_close()


def test_17_the_fixture_survives_a_traversal_attempt(admin):
    """A refusal must not damage the store it refused to serve."""
    tmp, srv = admin
    for bad in TRAVERSAL:
        _req(srv, f"/api/fixtures?upstream={bad}")
        _req(srv, f"/api/fixtures/{bad}/x", method="DELETE")
    assert [f.id for f in Store(tmp)._07()] == ["good"]


def test_18_a_directory_named_like_a_traversal_is_a_404_not_a_crash(admin):
    """`%2e%2e` as a literal name decodes to itself and simply does not exist."""
    _tmp, srv = admin
    status, raw = _req(srv, "/api/fixtures?upstream=%252e%252e")
    assert status in (200, 404), (status, raw)


def test_19_tempdir_is_usable_as_fixtures_root():
    with tempfile.TemporaryDirectory() as td:
        srv = _start(td)
        try:
            assert _req(srv, "/api/state")[0] == 200
        finally:
            srv.shutdown()
            srv.server_close()
