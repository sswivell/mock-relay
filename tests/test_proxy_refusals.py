"""Proxy behaviour when a request trips a deliberate refusal.

A MockRelayError is a decision, not a crash, so it has to reach the client
as an HTTP status. Before this guard existed, a rejected store path
escaped as a socketserver traceback and left the connection half-written.

Note the layering. The proxy resolves the upstream from the first path
segment and 502s an unknown one, so `GET /../x` never reaches the store.
The store is reached for a *configured* upstream, which is what this file
exercises: an upstream whose name the store refuses must still produce a
tidy 400. The traversal regressions that motivated the guard live in
tests/test_store_traversal.py and tests/test_admin_api.py.
"""

import http.client
import http.server
import json
import tempfile
import threading

from mockrelay._05 import _06 as Config
from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import _04 as Store
from mockrelay._11 import _01 as Metrics
from mockrelay._13 import _18 as State
from mockrelay._13 import _30 as start


def _upstream():
    """A tiny real HTTP server, so record mode actually reaches the store."""

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            return

        def do_GET(self):
            body = b'{"from":"upstream"}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _serve(td, upstreams=None, **cfg_kw):
    cfg = Config({
        "listen": "127.0.0.1:0",
        "admin_listen": "127.0.0.1:0",
        "fixtures_dir": td,
        "mode": "replay",
        "upstreams": upstreams or {"u": {"base_url": "http://127.0.0.1:9"}},
        **cfg_kw,
    })
    store = Store(cfg.fixtures_dir)
    store._06("u", _06(id="f1", upstream="u",
                       match=_01(method="GET", path="/x"),
                       request=_04(method="GET", path="/x"),
                       response=_05(status=200, body={"ok": 1})))
    srv = start(State(cfg, store, Metrics()))
    return cfg, srv


def _req(port, path, method="GET"):
    c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        c.request(method, path)
        r = c.getresponse()
        return r.status, r.read()
    finally:
        c.close()


def test_01_unknown_upstream_is_still_a_502():
    """The proxy gates on the configured upstream list before the store."""
    with tempfile.TemporaryDirectory() as td:
        _cfg, srv = _serve(td)
        try:
            port = srv.server_address[1]
            for path in ("/../x", "/..%2Fx", "/%2e%2e/x", "/a%00b/x"):
                status, raw = _req(port, path)
                assert status == 502, (path, status, raw)
                assert b"unknown upstream" in raw
        finally:
            srv.shutdown()
            srv.server_close()


def test_02_a_store_refusal_is_a_400_not_a_traceback():
    up = _upstream()
    try:
        base = f"http://127.0.0.1:{up.server_address[1]}"
        with tempfile.TemporaryDirectory() as td:
            _cfg, srv = _serve(
                td,
                upstreams={"bad:name": {"base_url": base}},
                mode="record",
            )
            try:
                port = srv.server_address[1]
                status, raw = _req(port, "/bad:name/x")
                assert status == 400, (status, raw)
                body = json.loads(raw)
                assert "error" in body
                assert "Traceback" not in body["error"]
                assert "socketserver" not in body["error"]
            finally:
                srv.shutdown()
                srv.server_close()
    finally:
        up.shutdown()
        up.server_close()


def test_02b_the_same_request_is_recorded_normally_for_a_valid_name():
    up = _upstream()
    try:
        base = f"http://127.0.0.1:{up.server_address[1]}"
        with tempfile.TemporaryDirectory() as td:
            cfg, srv = _serve(td, upstreams={"good": {"base_url": base}},
                              mode="record")
            try:
                port = srv.server_address[1]
                status, raw = _req(port, "/good/x")
                assert status == 200, (status, raw)
                assert json.loads(raw) == {"from": "upstream"}
                assert len(list(Store(cfg.fixtures_dir)._07("good"))) == 1
            finally:
                srv.shutdown()
                srv.server_close()
    finally:
        up.shutdown()
        up.server_close()


def test_03_the_connection_stays_usable_after_a_refusal():
    with tempfile.TemporaryDirectory() as td:
        _cfg, srv = _serve(
            td,
            upstreams={"bad:name": {"base_url": "http://127.0.0.1:9"},
                       "u": {"base_url": "http://127.0.0.1:9"}},
            mode="replay",
        )
        try:
            port = srv.server_address[1]
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            c.request("GET", "/u/../x")
            r = c.getresponse()
            r.read()
            c.request("GET", "/u/x")
            r2 = c.getresponse()
            assert r2.status == 200
            assert json.loads(r2.read()) == {"ok": 1}
            c.close()
        finally:
            srv.shutdown()
            srv.server_close()


def test_04_a_refusal_never_leaks_a_traceback():
    up = _upstream()
    try:
        base = f"http://127.0.0.1:{up.server_address[1]}"
        with tempfile.TemporaryDirectory() as td:
            _cfg, srv = _serve(
                td,
                upstreams={"bad:name": {"base_url": base}},
                mode="record",
            )
            try:
                port = srv.server_address[1]
                _status, raw = _req(port, "/bad:name/x")
                text = raw.decode()
                assert "Traceback" not in text
                assert "socketserver" not in text
                assert 'File "' not in text
            finally:
                srv.shutdown()
                srv.server_close()
    finally:
        up.shutdown()
        up.server_close()


def test_04_normal_requests_are_unaffected_by_the_guard():
    with tempfile.TemporaryDirectory() as td:
        _cfg, srv = _serve(td)
        try:
            port = srv.server_address[1]
            status, raw = _req(port, "/u/x")
            assert status == 200
            assert json.loads(raw) == {"ok": 1}
        finally:
            srv.shutdown()
            srv.server_close()
