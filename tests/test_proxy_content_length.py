"""A malformed Content-Length must be answered, not crash the connection.

The proxy framed its body with `int(self.headers.get("Content-Length", 0)
or 0)`. Every non-numeric shape raised ValueError from inside the
request handler, which BaseHTTPRequestHandler turns into a 500 with no
response and a dropped connection. A negative value did worse than
crash: `rfile.read(-5)` is not an error, it reads to end of stream, so
the request was framed by whatever the client sent next.

These go over a real socket because the failure was a transport-level
one: the client saw a reset, not a status.
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
from mockrelay._13 import _30 as start

MALFORMED = [
    "abc",
    "1e3",
    "0x10",
    "5.0",
    "-1",
    "-0",
    "+5",
    "1_000",
    "",
]

LEGAL = [("0", 0), ("2", 2), ("007", 7)]


def _serve(td):
    cfg = Config({
        "listen": "127.0.0.1:0",
        "admin_listen": "127.0.0.1:0",
        "fixtures_dir": td,
        "mode": "replay",
        "upstreams": {"u": {"base_url": "http://127.0.0.1:9"}},
    })
    store = Store(cfg.fixtures_dir)
    store._06("u", _06(id="f1", upstream="u",
                       match=_01(method="POST", path="/x", body_contains=None),
                       request=_04(method="POST", path="/x"),
                       response=_05(status=200, body={"ok": 1})))
    return start(State(cfg, store, Metrics()))


@pytest.fixture
def proxy():
    with tempfile.TemporaryDirectory() as td:
        srv = _serve(td)
        try:
            yield srv
        finally:
            srv.shutdown()
            srv.server_close()


def _raw_post(srv, declared, body=b"{}"):
    """Send a hand-written request so the header value is exactly as given.

    The timeout is short on purpose. Pre-fix, a value int() tolerates but
    HTTP does not (such as "5 ") made the server wait for bytes that never
    arrived, so a missing 400 shows up as a slow failure rather than a
    hang that stalls the suite.
    """
    c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=3)
    try:
        c.putrequest("POST", "/u/x", skip_host=False)
        c.putheader("Host", "127.0.0.1")
        c.putheader("Content-Type", "application/json")
        c.putheader("Content-Length", declared)
        c.endheaders()
        c.send(body)
        r = c.getresponse()
        return r.status, r.read()
    finally:
        c.close()


def _is_reset(exc):
    return isinstance(exc, (http.client.RemoteDisconnected,
                            ConnectionResetError, TimeoutError,
                            OSError))


@pytest.mark.parametrize("declared", MALFORMED)
def test_01_malformed_content_length_gets_a_400(proxy, declared):
    try:
        status, raw = _raw_post(proxy, declared)
    except (http.client.RemoteDisconnected, ConnectionResetError,
            TimeoutError) as e:
        pytest.fail(f"{declared!r} dropped the connection: {e!r}")
    assert status == 400, (declared, status, raw)
    body = json.loads(raw)
    assert "Content-Length" in body["error"], body
    assert "Traceback" not in body["error"]


@pytest.mark.parametrize("declared", MALFORMED)
def test_02_malformed_content_length_never_resets_the_connection(proxy, declared):
    """The client must get a real response, not a reset or a stall."""
    try:
        status, raw = _raw_post(proxy, declared)
    except Exception as e:
        if _is_reset(e):
            pytest.fail(f"{declared!r} dropped the connection: {e!r}")
        raise
    assert status in (400, 404), (declared, status, raw)


@pytest.mark.parametrize("declared", ["-1", "-0", "-99999999"])
def test_03_a_negative_content_length_is_refused(proxy, declared):
    """`rfile.read(-n)` reads to EOF, which silently reframes the request."""
    try:
        status, raw = _raw_post(proxy, declared)
    except Exception as e:
        if _is_reset(e):
            pytest.fail(f"{declared!r} dropped the connection: {e!r}")
        raise
    assert status == 400, (declared, status, raw)


@pytest.mark.parametrize("declared,size", LEGAL)
def test_04_legal_content_lengths_still_work(proxy, declared, size):
    payload = b"{" * size
    status, raw = _raw_post(proxy, declared, payload)
    assert status == 200, (declared, status, raw)
    assert json.loads(raw) == {"ok": 1}


def test_05_a_malformed_value_is_refused_before_the_upstream_is_contacted():
    """No outbound request may be made on a request we cannot frame."""
    with tempfile.TemporaryDirectory() as td:
        cfg = Config({
            "listen": "127.0.0.1:0",
            "admin_listen": "127.0.0.1:0",
            "fixtures_dir": td,
            "mode": "record",
            "upstreams": {"u": {"base_url": "http://127.0.0.1:9"}},
        })
        srv = start(State(cfg, Store(cfg.fixtures_dir), Metrics()))
        try:
            status, raw = _raw_post(srv, "abc")
            assert status == 400, (status, raw)
            assert not list(Store(td)._07("u")), "a fixture was recorded anyway"
        finally:
            srv.shutdown()
            srv.server_close()


def test_06_many_malformed_requests_do_not_wedge_the_listener(proxy):
    results = []

    def worker(value):
        try:
            results.append(_raw_post(proxy, value)[0])
        except Exception as e:
            results.append(repr(e))

    threads = [threading.Thread(target=worker, args=(v,))
               for v in MALFORMED * 2]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)
    assert results == [400] * len(MALFORMED * 2), results
