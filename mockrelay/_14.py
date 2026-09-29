"""Admin HTTP server: JSON API endpoints, match probing and fixture management."""
from __future__ import annotations

import functools
import http.server
import json
import threading
from urllib.parse import parse_qs, parse_qsl, urlparse

from ._09 import _22 as _11
from ._09 import _29 as _12
from ._12 import _06 as _03
from ._13 import _18 as _01
from ._13 import _29 as _02
from .errors import LimitExceeded, MockRelayError, SecurityError

_04 = """<!doctype html><html><head><title>MockRelay</title>
<style>
 body{font-family:ui-sans-serif,system-ui;margin:2rem;max-width:960px;background:#0b1220;color:#e0f2fe}
 h1{color:#7dd3fc}
 table{border-collapse:collapse;width:100%}
 th,td{border-bottom:1px solid #1e3a5f;padding:.4rem .6rem;text-align:left;font-size:.9rem}
 code{background:#152a47;padding:.1rem .3rem;border-radius:4px;color:#bae6fd}
 .pill{padding:.15rem .5rem;border-radius:999px;background:#152a47;color:#7dd3fc;font-size:.75rem}
</style></head><body>
<h1>MockRelay</h1>
<p>Mode: <span class="pill" id="mode">-</span> &nbsp; Latency: <span class="pill" id="lat">-</span> ms
 &nbsp; Hits: <span class="pill" id="hits">-</span> &nbsp; Misses: <span class="pill" id="miss">-</span>
 &nbsp; Recorded: <span class="pill" id="rec">-</span></p>
<h2>Recent traffic</h2>
<table id="recent"><thead><tr><th>Time</th><th>Method</th><th>Path</th><th>Status</th><th>Mode</th></tr></thead><tbody></tbody></table>
<h2>Fixtures</h2>
<table id="fx"><thead><tr><th>Upstream</th><th>ID</th><th>Method</th><th>Path</th><th>Status</th></tr></thead><tbody></tbody></table>
<script>
async function refresh(){
  const s = await (await fetch('/api/state')).json();
  mode.textContent = s.mode; lat.textContent = s.latency_ms;
  hits.textContent = s.hits; miss.textContent = s.misses; rec.textContent = s.recorded;
  const r = await (await fetch('/api/recent')).json();
  const rb = document.querySelector('#recent tbody'); rb.replaceChildren();
    for (const x of r){
      const tr=document.createElement('tr');
      for (const v of [x.t, x.m, x.p, x.s, x.mode]) {
        const td = document.createElement('td');
        // textContent, never a markup assignment: a recorded path is
        // attacker-supplied data, and interpolating it into markup would
        // execute on every dashboard load for whoever has the admin port
        // open. tests/test_admin_dashboard_xss.py enforces this.
        td.textContent = v; tr.appendChild(td);
      }
      rb.appendChild(tr);}
  const fx = await (await fetch('/api/fixtures')).json();
  const tb = document.querySelector('#fx tbody'); tb.replaceChildren();
  for (const f of fx){
    const tr = document.createElement('tr');
    const cells = [f.upstream, null, f.match && f.match.method,
                   f.match && f.match.path,
                   f.response && f.response.status];
    cells.forEach((v, i) => {
      const td = document.createElement('td');
      if (i === 1) { const c = document.createElement('code'); c.textContent = f.id; td.appendChild(c); }
      else { td.textContent = v; }
      tr.appendChild(td);
    });
    tb.appendChild(tr);}
}
refresh(); setInterval(refresh, 2000);
</script></body></html>"""


def _18(fn):
    """Drain the request body, then map MockRelay errors onto statuses.

    Without this a traversal attempt in the upstream segment reaches the
    store, raises SecurityError, and escapes through
    BaseHTTPRequestHandler as a 500 with a traceback on stderr and a
    dropped connection.
    """

    @functools.wraps(fn)
    def _19(self):
        self._15()
        try:
            return fn(self)
        except MockRelayError as e:
            # `code` is the stable token; `kind` is a phrase meant for
            # people and may be reworded without warning.
            if isinstance(e, SecurityError):
                status = 400
            elif isinstance(e, LimitExceeded):
                status = e.status
            else:
                status = 500
            return self._07(status, {
                "error": e.message or e.kind,
                "type": e.code,
                "kind": e.kind,
            })

    return _19


def _05(state: _01):
    cfg = state.cfg
    store = state.store
    metrics = state.metrics

    class _06(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            return

        def _07(self, status: int, payload):
            body = json.dumps(payload, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _08(self, html: str):
            body = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _09(self, body: bytes, ctype: str = "text/plain"):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _15(self):
            """Consume any unread request body.

            No admin route reads one, but HTTP/1.1 keep-alive means the
            next request on the connection is read from wherever the
            last one stopped. Leaving bytes in rfile makes the following
            request start mid-body and fail to parse.
            """
            try:
                remaining = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return
            if remaining <= 0:
                return
            limit = int(getattr(cfg, "max_body_bytes", 0) or 0) or 1 << 20
            remaining = min(remaining, limit)
            while remaining > 0:
                chunk = self.rfile.read(min(remaining, 65536))
                if not chunk:
                    break
                remaining -= len(chunk)


        @_18
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                return self._08(_04)
            if self.path == "/metrics":
                return self._09(metrics._08().encode(), "text/plain; version=0.0.4")
            if self.path == "/api/state":
                return self._07(200, {
                    "mode": cfg.mode, "latency_ms": cfg.latency_ms,
                    "upstreams": list(cfg.upstreams.keys()),
                })
            if self.path == "/api/recent":
                return self._07(200, metrics._09())
            if self.path.startswith("/api/match"):
                p = urlparse(self.path)
                q = parse_qs(p.query)
                upstream = (q.get("upstream") or [None])[0]
                method = (q.get("method") or ["GET"])[0].upper()
                path = (q.get("path") or ["/"])[0]
                qq: dict[str, list[str]] = {}
                for k, v in parse_qsl((q.get("query") or [""])[0],
                                      keep_blank_values=True):
                    qq.setdefault(k, []).append(v)
                body = None
                raw_body = (q.get("body") or [None])[0]
                if raw_body is not None:
                    try:
                        body = json.loads(raw_body)
                    except ValueError:
                        body = raw_body
                opts = _12(cfg._12(upstream or "", path))
                rows = _11(list(store._07(upstream)), method, path, qq,
                           body, opts)
                return self._07(200, {
                    "upstream": upstream,
                    "method": method,
                    "path": path,
                    "match_mode": opts.mode,
                    "fuzzy_threshold": opts.threshold,
                    "ignore_case": opts.ignore_case,
                    "fuzzy_enabled": opts.fuzzy_enabled,
                    "match_priority": list(opts.order),
                    "results": rows,
                })
            if self.path.startswith("/api/fixtures"):
                upstream = None
                if "?" in self.path:
                    q = parse_qs(urlparse(self.path).query)
                    upstream = (q.get("upstream") or [None])[0]
                out: list[dict] = []
                for f in store._07(upstream):
                    out.append(f._07())
                return self._07(200, out)
            return self._07(404, {"error": "not found"})

        @_18
        def do_POST(self):
            p = urlparse(self.path).path
            parts = p.strip("/").split("/")
            if len(parts) == 3 and parts[0] == "api" and parts[1] == "mode":
                m = parts[2]
                if m not in ("record", "replay", "passthrough", "hybrid"):
                    return self._07(400, {"error": "invalid mode"})
                cfg.mode = m
                return self._07(200, {"mode": cfg.mode})
            if len(parts) == 3 and parts[0] == "api" and parts[1] == "latency":
                try:
                    cfg.latency_ms = max(0, int(parts[2]))
                except ValueError:
                    return self._07(400, {"error": "bad ms"})
                return self._07(200, {"latency_ms": cfg.latency_ms})
            return self._07(404, {"error": "not found"})

        @_18
        def do_DELETE(self):
            p = urlparse(self.path).path
            parts = p.strip("/").split("/")
            if len(parts) == 4 and parts[0] == "api" and parts[1] == "fixtures":
                ok = store._08(parts[2], parts[3])
                return self._07(200 if ok else 404, {"deleted": ok})
            return self._07(404, {"error": "not found"})

    return _06


def _10(state: _01):
    host, port = _03(state.cfg.admin_listen)
    handler = _05(state)
    srv = _02((host, port), handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv
