"""What the recorder writes to disk, and what it must never write.

A fixture file is the longest-lived artifact this tool produces. It gets
committed, attached to a bug, and pasted into a chat. Anything the
redaction settings are meant to keep out of it has to stay out, which
means the redaction has to be applied on the way *into* the store and not
only on the way out of a request.

The tests drive a real record cycle against a real socket, because the
defect being pinned here is in the middle of the record path and cannot be
reached by calling the store directly.
"""

from __future__ import annotations

import http.client
import http.server
import json
import tempfile
import threading

import pytest

from mockrelay._05 import _06 as Config
from mockrelay._10 import _04 as Store
from mockrelay._11 import _01 as Metrics
from mockrelay._13 import _18 as State
from mockrelay._13 import _30 as start

SECRET = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ012345"


def _upstream(status=200, body=None, headers=None):
    """A real origin that returns whatever the test wants recorded."""

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            return

        def _drain(self):
            """Consume the request body before answering.

            This handler speaks HTTP/1.1, so the connection is kept alive. An
            origin that answers without reading the request body leaves those
            bytes in the socket buffer, and the close that follows is then
            turned into a TCP reset. The proxy reads that reset as a failed
            upstream call and returns 502, which showed up here as a
            fixture-count failure in roughly one run out of five. Draining
            first keeps the exchange in a state both sides agree on.
            """
            length = int(self.headers.get("Content-Length") or 0)
            if length:
                self.rfile.read(length)

        def do_GET(self):
            self._drain()
            payload = json.dumps(body or {"ok": True}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_POST(self):
            self.do_GET()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _record(td, *, upstream=None, body=None, **cfg_kw):
    """Run one record cycle, returning the store and the client response."""
    up = upstream or _upstream()
    cfg = Config(
        {
            "listen": "127.0.0.1:0",
            "admin_listen": "127.0.0.1:0",
            "fixtures_dir": td,
            "mode": "record",
            "upstreams": {
                "u": {"base_url": f"http://127.0.0.1:{up.server_address[1]}"}
            },
            **cfg_kw,
        }
    )
    store = Store(cfg.fixtures_dir)
    srv = start(State(cfg, store, Metrics()))
    payload = json.dumps(body).encode() if body is not None else None
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
        c.request(
            "POST" if payload else "GET",
            "/u/things",
            payload,
            {
                "Authorization": f"Bearer {SECRET}",
                **({"Content-Type": "application/json"} if payload else {}),
            },
        )
        r = c.getresponse()
        out = (r.status, dict(r.getheaders()), r.read())
        c.close()
    finally:
        srv.shutdown()
    return store, out


def _only(store):
    files = list(store.root.rglob("*.json"))
    assert len(files) == 1, [str(f) for f in files]
    return files[0]


@pytest.fixture
def td():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_01_the_client_still_gets_the_real_response(td):
    _store, (status, _hdrs, raw) = _record(td)
    assert status == 200
    assert json.loads(raw) == {"ok": True}


def test_02_a_token_in_the_response_body_is_not_written(td):
    store, _ = _record(
        td, upstream=_upstream(body={"user": "octocat", "token": SECRET})
    )
    text = _only(store).read_text(encoding="utf-8")
    assert SECRET not in text


def test_03_a_bearer_header_in_a_string_body_is_not_written(td):
    store, _ = _record(
        td, upstream=_upstream(body={"note": f"use Bearer {SECRET} to call"})
    )
    text = _only(store).read_text(encoding="utf-8")
    assert SECRET not in text


def test_04_a_nested_token_is_not_written(td):
    store, _ = _record(td, upstream=_upstream(body={"a": [{"b": {"c": SECRET}}]}))
    text = _only(store).read_text(encoding="utf-8")
    assert SECRET not in text


def test_05_a_stripe_key_in_the_response_body_is_not_written(td):
    store, _ = _record(td, upstream=_upstream(body={"key": "sk_live_ABCDEFGHIJKLMNOP"}))
    text = _only(store).read_text(encoding="utf-8")
    assert "sk_live_ABCDEFGHIJKLMNOP" not in text


def test_06_a_configured_response_header_is_not_written(td):
    store, _ = _record(
        td,
        upstream=_upstream(headers={"X-Api-Key": "upstream-secret"}),
        redact_headers=["authorization", "x-api-key"],
    )
    doc = json.loads(_only(store).read_text(encoding="utf-8"))
    assert doc["response"]["headers"]["X-Api-Key"] == "{{SECRET}}"
    assert "upstream-secret" not in _only(store).read_text(encoding="utf-8")


def test_07_an_unconfigured_response_header_is_left_alone(td):
    store, _ = _record(
        td,
        upstream=_upstream(headers={"X-Trace": "keepme"}),
        redact_headers=["authorization"],
    )
    text = _only(store).read_text(encoding="utf-8")
    assert "keepme" in text


def test_08_the_request_side_is_still_redacted(td):
    """The request path already worked; this pins it against regression."""
    store, _ = _record(td, redact_headers=["authorization"])
    text = _only(store).read_text(encoding="utf-8")
    assert SECRET not in text


def test_08b_a_token_in_a_json_request_body_is_not_written(td):
    """A dict body took the unredacted branch; a str body was scrubbed."""
    store, _ = _record(td, body={"name": "octocat", "token": SECRET})
    text = _only(store).read_text(encoding="utf-8")
    assert SECRET not in text


def test_08c_a_json_request_body_keeps_its_other_fields(td):
    store, _ = _record(td, body={"name": "octocat", "token": SECRET})
    body = json.loads(_only(store).read_text(encoding="utf-8"))["request"]["body"]
    assert body["name"] == "octocat"
    assert body["token"] != SECRET


def test_09_the_non_secret_values_survive(td):
    store, _ = _record(
        td, upstream=_upstream(body={"login": "octocat", "count": 7, "token": SECRET})
    )
    body = json.loads(_only(store).read_text(encoding="utf-8"))["response"]["body"]
    assert body["login"] == "octocat"
    assert body["count"] == 7
    assert body["token"] != SECRET


def test_10_the_status_and_path_are_untouched(td):
    store, _ = _record(td, upstream=_upstream(status=201, body={"token": SECRET}))
    doc = json.loads(_only(store).read_text(encoding="utf-8"))
    assert doc["response"]["status"] == 201
    assert doc["request"]["path"] == "/things"


def test_11_a_json_body_is_rewritten_not_mangled(td):
    store, _ = _record(
        td, upstream=_upstream(body={"token": SECRET, "nested": {"deep": [1, 2, 3]}})
    )
    body = json.loads(_only(store).read_text(encoding="utf-8"))["response"]["body"]
    assert body["nested"] == {"deep": [1, 2, 3]}


def test_12_the_recorded_fixture_still_replays(td):
    """Redaction that breaks matching would defeat the point of recording."""
    _record(td, upstream=_upstream(body={"token": SECRET}))
    cfg = Config(
        {
            "listen": "127.0.0.1:0",
            "admin_listen": "127.0.0.1:0",
            "fixtures_dir": td,
            "mode": "replay",
            "upstreams": {"u": {"base_url": "http://127.0.0.1:9"}},
        }
    )
    srv = start(State(cfg, Store(cfg.fixtures_dir), Metrics()))
    try:
        c = http.client.HTTPConnection("127.0.0.1", srv.server_address[1], timeout=5)
        c.request("GET", "/u/things")
        r = c.getresponse()
        assert r.status == 200
        assert SECRET not in r.read().decode()
        c.close()
    finally:
        srv.shutdown()
