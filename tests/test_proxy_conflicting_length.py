"""Two Content-Length headers must not be resolved by guessing.

RFC 7230 section 3.3.2 draws the line in a specific place:

  * identical duplicates -- "2" and "2", or the single field "2, 2" -- may
    be accepted, because there is no disagreement about where the body
    ends;
  * conflicting duplicates -- "2" and "5" -- must be rejected, because
    that disagreement is the whole of request smuggling.

Python's http.client does not help here. `headers.get("Content-Length")`
returns only the *first* value, so a request declaring 2 and then 5 was
read as a 2-byte body and the rest was treated as the start of the next
request on the connection. It is not joined with a comma either; the
comma-joined shape only appears when a client builds the header itself.

Transfer-Encoding alongside Content-Length is the other half of the rule,
and nothing in the stdlib flags it: a chunked request was silently
treated as having no body.
"""

import http.client
import json
import socket
import tempfile

import pytest

from mockrelay._05 import _06 as Config
from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import _04 as Store
from mockrelay._11 import _01 as Metrics
from mockrelay._13 import _18 as State
from mockrelay._13 import _30 as start

CONFLICTING = [
    ["Content-Length: 2", "Content-Length: 5"],
    ["Content-Length: 0", "Content-Length: 99"],
    ["Content-Length: 5", "Content-Length: 2"],
    ["Content-Length: 2", "Content-Length: 2", "Content-Length: 5"],
    ["Content-Length: 0", "Content-Length: 1", "Content-Length: 2"],
]

CONFLICTING_JOINED = [
    ["Content-Length: 2, 5"],
    ["Content-Length: 2,5"],
]

IDENTICAL = [
    ["Content-Length: 2", "Content-Length: 2"],
    ["Content-Length: 2, 2"],
    ["Content-Length: 2,2"],
    ["Content-Length: 2", "Content-Length: 2", "Content-Length: 2"],
]


def _serve(td, mode="replay"):
    cfg = Config({
        "listen": "127.0.0.1:0",
        "admin_listen": "127.0.0.1:0",
        "fixtures_dir": td,
        "mode": mode,
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


def _raw(srv, lines, body=b"{}"):
    """Send a request with exactly the header lines given, over a socket.

    Raw bytes rather than http.client, because http.client cannot express
    a repeated Content-Length: it would overwrite the first with the
    second. The repeated header is the entire point of these tests.
    """
    head = ["POST /u/x HTTP/1.1", "Host: 127.0.0.1",
            "Content-Type: application/json", *lines, "", ""]
    sock = socket.create_connection(("127.0.0.1", srv.server_address[1]),
                                    timeout=5)
    sock.settimeout(5)
    sock.sendall(("\r\n".join(head) + "\r\n").encode("latin-1") + body)
    return sock


def _status(srv, lines, body=b"{}"):
    sock = _raw(srv, lines, body)
    try:
        buf = b""
        while b"\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        if not buf:
            pytest.fail("server closed without responding")
        return buf.split(b"\r\n", 1)[0].decode("latin-1")
    finally:
        sock.close()


@pytest.mark.parametrize("lines", CONFLICTING)
def test_01_conflicting_content_length_fields_are_refused(proxy, lines):
    assert " 400 " in _status(proxy, lines), lines


@pytest.mark.parametrize("lines", CONFLICTING + CONFLICTING_JOINED)
def test_02_conflicting_lengths_record_no_fixture(lines):
    """A smuggled request must not produce a stored response."""
    with tempfile.TemporaryDirectory() as td:
        srv = _serve(td, mode="record")
        try:
            _status(srv, lines)
        finally:
            srv.shutdown()
            srv.server_close()
        assert [f.id for f in Store(td)._07("u")] == ["f1"], lines


@pytest.mark.parametrize("lines", IDENTICAL)
def test_03_identical_duplicates_are_accepted(proxy, lines):
    """The RFC permits this, and http.client itself produces it."""
    assert " 200 " in _status(proxy, lines), lines


def test_04_content_length_with_transfer_encoding_is_refused(proxy):
    assert " 400 " in _status(
        proxy, ["Content-Length: 2", "Transfer-Encoding: chunked"],
        body=b"2\r\n{}\r\n0\r\n\r\n")


def test_05_transfer_encoding_alone_is_refused_rather_than_ignored(proxy):
    """A chunked body was silently treated as a zero-length body."""
    assert " 400 " in _status(
        proxy, ["Transfer-Encoding: chunked"],
        body=b"2\r\n{}\r\n0\r\n\r\n")


def test_06_no_framing_headers_at_all_is_a_normal_request(proxy):
    assert " 200 " in _status(proxy, [])


def test_07_the_error_body_names_the_framing_problem(proxy):
    c = http.client.HTTPConnection("127.0.0.1", proxy.server_address[1],
                                   timeout=5)
    try:
        c.putrequest("POST", "/u/x")
        c.putheader("Host", "127.0.0.1")
        c.putheader("Content-Length", "2, 5")
        c.endheaders()
        c.send(b"{}")
        r = c.getresponse()
        status, raw = r.status, r.read()
    finally:
        c.close()
    assert status == 400, (status, raw)
    body = json.loads(raw)
    assert "Content-Length" in body["error"], body


def test_08_a_smuggled_prefix_is_not_left_in_the_buffer(proxy):
    """After a 400 the connection must not be reusable for a smuggle.

    If the conflicting body was left unread, the next request on the
    connection would be read starting in the middle of it.
    """
    sock = _raw(proxy, ["Content-Length: 2", "Content-Length: 5"],
                body=b"{}SMUGGLED")
    try:
        buf = b""
        while b"\r\n" not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
        assert b" 400 " in buf.split(b"\r\n", 1)[0], buf[:80]
        sock.settimeout(2)
        try:
            leftover = sock.recv(4096)
        except TimeoutError:
            leftover = b""
        assert b"HTTP/1.1 200" not in leftover, leftover
    finally:
        sock.close()


def test_09_hop_by_hop_transfer_encoding_variants_are_all_refused(proxy):
    for te in ("chunked", "identity", "gzip, chunked", " chunked"):
        assert " 400 " in _status(
            proxy, [f"Transfer-Encoding: {te}"],
            body=b"2\r\n{}\r\n0\r\n\r\n"), te
