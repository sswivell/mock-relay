"""A refused request must not leave the connection in a usable state.

When the proxy refuses a request it has no way to know where the body
ends -- that is precisely why it refused. The bytes stay in the socket.
With keep-alive, the next iteration of the request loop then read them as
a request line, which meant a client could choose what the server
parsed next, and every refusal printed a traceback to stderr.

The fix is to close rather than guess. Everything here is about the
second response: there must not be one.
"""

import socket
import tempfile

import pytest

from mockrelay._05 import _06 as Config
from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import _04 as Store
from mockrelay._11 import _01 as Metrics
from mockrelay._13 import _18 as State
from mockrelay._13 import _30 as start

# A second request spliced onto the body of the first. If the server
# fails to close, it reads these bytes and serves a 200.
SMUGGLED = b"{}GET /u/x HTTP/1.1\r\nHost: h\r\nContent-Length: 2\r\n\r\n{}"


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
                       match=_01(method="POST", path="/x"),
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


def _exchange(srv, lines, body):
    head = ["POST /u/x HTTP/1.1", "Host: 127.0.0.1", *lines, "", ""]
    s = socket.create_connection(("127.0.0.1", srv.server_address[1]),
                                timeout=5)
    s.settimeout(3)
    s.sendall(("\r\n".join(head) + "\r\n").encode("latin-1") + body)
    data = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    except (TimeoutError, ConnectionError):
        pass
    finally:
        s.close()
    return data


REFUSED = [
    ["Content-Length: 2", "Content-Length: 5"],
    ["Content-Length: 2, 5"],
    ["Transfer-Encoding: chunked"],
    ["Content-Length: 2", "Transfer-Encoding: chunked"],
    ["Content-Length: abc"],
    ["Content-Length: -1"],
]


@pytest.mark.parametrize("lines", REFUSED)
def test_01_a_refused_request_never_gets_a_second_response(proxy, lines):
    data = _exchange(proxy, lines, SMUGGLED)
    assert data.count(b"HTTP/1.1 ") == 1, data[:200]
    assert b" 400 " in data.split(b"\r\n", 1)[0], data[:200]


@pytest.mark.parametrize("lines", REFUSED)
def test_02_a_refused_request_announces_that_it_is_closing(proxy, lines):
    data = _exchange(proxy, lines, SMUGGLED)
    assert b"Connection: close" in data, data[:300]


def test_03_a_well_formed_request_still_keeps_the_connection_open(proxy):
    """Only refused framing closes. A normal response must not."""
    data = _exchange(proxy, ["Content-Length: 2"], b"{}")
    assert b" 200 " in data.split(b"\r\n", 1)[0], data[:200]
    assert b"Connection: close" not in data, data[:300]


def test_04_the_spliced_request_would_otherwise_have_matched(proxy):
    """Guards the fixture: without this, a 200 would prove nothing.

    The same request line that gets spliced onto a refused body, sent on
    its own, matches the fixture and returns 200. So a second response
    appearing in test_01 is the server reading our bytes, not a fixture
    that was always going to match.
    """
    data = _exchange(proxy, ["Content-Length: 2"],
                     b"{}")
    assert b" 200 " in data.split(b"\r\n", 1)[0], data[:200]
