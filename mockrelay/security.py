"""Filesystem, network, and header safety primitives.

Everything that turns user-controlled or operator-controlled text into a path,
a socket address, or an outgoing header goes through this module.
"""

from __future__ import annotations

import ipaddress
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .errors import ConfigError, FramingError, Problem, SecurityError

__all__ = [
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "HOP_BY_HOP_HEADERS",
    "LOOPBACK_HOST_NAMES",
    "ListenAddress",
    "check_request_framing",
    "ensure_writable_dir",
    "is_loopback",
    "is_valid_header_name",
    "is_valid_header_value",
    "is_within",
    "parse_content_length",
    "parse_content_length_fields",
    "parse_listen",
    "render_listen",
    "safe_child",
    "safe_repr",
    "sanitize_headers",
    "temporary_free_mb",
    "validate_component",
]

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080

LOOPBACK_HOST_NAMES = frozenset(
    (
        "localhost",
        "localhost.localdomain",
        "ip6-localhost",
        "ip6-loopback",
    )
)

HOP_BY_HOP_HEADERS = frozenset(
    (
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "trailers",
        "transfer-encoding",
        "upgrade",
        "host",
        "content-length",
        "proxy-connection",
    )
)

_HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
_BAD_COMPONENT_RE = re.compile(r"[\x00-\x1f\x7f<>:\"|?*\\/]")
_WINDOWS_RESERVED = frozenset(
    (
        "con",
        "prn",
        "aux",
        "nul",
        *(f"com{i}" for i in range(1, 10)),
        *(f"lpt{i}" for i in range(1, 10)),
    )
)
MAX_COMPONENT_LEN = 128
MAX_LISTEN_LEN = 300


def is_valid_header_name(name: str) -> bool:
    return bool(name) and len(name) <= 256 and bool(_HEADER_NAME_RE.match(name))


def is_valid_header_value(value: object) -> bool:
    if not isinstance(value, str):
        return True
    if len(value) > 16384:
        return False
    return not any(ch in value for ch in ("\r", "\n", "\x00"))


def is_loopback(host: str) -> bool:
    """True only for addresses that cannot leave this machine.

    A hostname that is not a known loopback name is treated as non-loopback,
    so an unresolvable or spoofed name never counts as safe.
    """
    name = (host or "").strip().strip("[]").lower()
    if not name:
        return True
    if name in LOOPBACK_HOST_NAMES:
        return True
    try:
        return ipaddress.ip_address(name).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class ListenAddress:
    host: str
    port: int
    spec: str = ""

    @property
    def loopback(self) -> bool:
        return is_loopback(self.host)

    @property
    def public(self) -> bool:
        return not self.loopback

    def render(self) -> str:
        return render_listen(self.host, self.port)


def render_listen(host: str, port: int) -> str:
    if ":" in host and not host.startswith("["):
        return f"[{host}]:{port}"
    return f"{host}:{port}"


def parse_listen(
    spec: object, default_port: int = DEFAULT_PORT, what: str = "listen"
) -> ListenAddress:
    """Parse ``host:port``, ``:port``, ``port``, or ``[v6]:port``."""
    problems: list[Problem] = []
    raw = str(spec if spec is not None else "").strip()
    if not raw:
        raw = render_listen(DEFAULT_HOST, default_port)
    if len(raw) > MAX_LISTEN_LEN:
        raise ConfigError(
            [Problem(f"`{what}` is longer than {MAX_LISTEN_LEN} characters")],
            hint="Use a short address such as 127.0.0.1:8080.",
        )
    host = ""
    port_text = ""
    if raw.startswith("["):
        end = raw.find("]")
        if end == -1:
            problems.append(
                Problem(
                    "unbalanced brackets in an IPv6 address",
                    subject=f"`{what}`",
                    expected="[::1]:8080",
                    location=raw,
                )
            )
        else:
            host = raw[1:end]
            rest = raw[end + 1 :]
            if rest.startswith(":"):
                port_text = rest[1:]
            elif rest:
                problems.append(
                    Problem(
                        "unexpected characters after the IPv6 address",
                        subject=f"`{what}`",
                        expected="[::1]:8080",
                        location=raw,
                    )
                )
    elif raw.count(":") > 1:
        host = raw
    elif ":" in raw:
        host, _, port_text = raw.partition(":")
    elif raw.isdigit():
        port_text = raw
    else:
        host = raw
    host = host.strip().strip("[]")
    port = default_port
    if port_text.strip():
        text = port_text.strip()
        if not text.isdigit():
            problems.append(
                Problem(
                    "port is not a number",
                    subject=f"`{what}`",
                    expected="0-65535",
                    location=raw,
                )
            )
        else:
            port = int(text)
            if not 0 <= port <= 65535:
                problems.append(
                    Problem(
                        f"port {port} is out of range",
                        subject=f"`{what}`",
                        expected="0-65535",
                        location=raw,
                    )
                )
    if not host:
        host = DEFAULT_HOST
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in host):
        problems.append(
            Problem(
                "host contains whitespace or control characters",
                subject=f"`{what}`",
                expected="127.0.0.1",
                location=raw,
            )
        )
    elif len(host) > 253:
        problems.append(
            Problem(
                "host is longer than 253 characters",
                subject=f"`{what}`",
                expected="127.0.0.1",
                location=raw,
            )
        )
    elif not _is_plausible_host(host):
        problems.append(
            Problem(
                "host is not a valid hostname or IP address",
                subject=f"`{what}`",
                expected="127.0.0.1 or localhost",
                location=raw,
            )
        )
    if problems:
        raise ConfigError(problems, hint="Use `host:port`, for example 127.0.0.1:8080.")
    return ListenAddress(host=host, port=port, spec=raw)


_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)[A-Za-z0-9_](?:[A-Za-z0-9_-]{0,61}"
    r"[A-Za-z0-9_])?(?:\.[A-Za-z0-9_](?:[A-Za-z0-9_-]{0,61}"
    r"[A-Za-z0-9_])?)*\.?$"
)


def _is_plausible_host(host: str) -> bool:
    if not host:
        return False
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        pass
    if host.endswith("."):
        host = host[:-1]
    return bool(_HOSTNAME_RE.match(host))


def validate_component(value: object, kind: str = "name") -> str:
    """Return ``value`` if it is safe to use as one path component."""
    text = str(value if value is not None else "")
    if not text:
        raise SecurityError(f"empty {kind} is not allowed")
    if text in (".", ".."):
        raise SecurityError(f"{kind} {text!r} is not allowed")
    if len(text) > MAX_COMPONENT_LEN:
        raise SecurityError(f"{kind} is longer than {MAX_COMPONENT_LEN} characters")
    if text.startswith("."):
        raise SecurityError(f"{kind} may not start with a dot: {text!r}")
    bad = _BAD_COMPONENT_RE.search(text)
    if bad:
        raise SecurityError(
            f"{kind} contains an illegal character ({bad.group(0)!r}): {text!r}"
        )
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        raise SecurityError(f"{kind} contains a control character: {text!r}")
    if text != text.strip() or text.endswith("."):
        raise SecurityError(
            f"{kind} may not have leading or trailing whitespace or a "
            f"trailing dot: {text!r}"
        )
    stem = text.split(".")[0].lower()
    if stem in _WINDOWS_RESERVED:
        raise SecurityError(f"{kind} {text!r} is a reserved device name on Windows")
    return text


def _norm(path: Path) -> str:
    """Canonical, symlink-resolved form of ``path`` for containment checks.

    ``resolve()`` matters here: a symlink inside the root would otherwise let a
    child escape while every textual component still looks safe.
    """
    return os.path.normcase(str(Path(path).resolve()))


def is_within(root: Path, child: Path) -> bool:
    base = _norm(root)
    target = _norm(child)
    return target == base or target.startswith(base + os.sep)


def safe_child(root: Path, *parts: str) -> Path:
    """Join ``parts`` under ``root`` and refuse anything that escapes it.

    Resolution is done with ``realpath`` so a symlink inside the root cannot
    be used to read or write outside it.
    """
    base = Path(os.path.realpath(str(root)))
    if not parts:
        return base
    checked = [validate_component(p, "path segment") for p in parts]
    candidate = base.joinpath(*checked)
    real = Path(os.path.realpath(str(candidate)))
    if not is_within(base, real):
        raise SecurityError(
            f"refusing to use {str(candidate)!r}: it resolves outside {str(base)!r}"
        )
    return candidate


def safe_repr(value: object, limit: int = 32) -> str:
    """Render ``value`` for an error message without risking the renderer.

    An error message that quotes hostile input can be the thing that
    breaks: the value is attacker-controlled, and a character outside the
    console encoding makes ``print`` raise while the diagnostic is being
    composed. MockRelay writes errors to a real console, which on Windows
    is routinely cp1252.

    So: ASCII-only, escaped, and truncated. The point of a message here is
    to say *what shape* was wrong, not to reproduce the payload.
    """
    text = value if isinstance(value, str) else str(value)
    clipped = text[:limit]
    if len(text) > limit:
        clipped += "..."
    return clipped.encode("ascii", "backslashreplace").decode("ascii")


def parse_content_length_fields(values: object, *, max_digits: int = 18) -> int:
    """Resolve every ``Content-Length`` a request carries into one length.

    ``http.server`` exposes repeated headers through ``get_all``, and
    ``headers.get`` would hand back only the first. That is not a
    simplification, it is the smuggling bug: a request declaring
    ``Content-Length: 2`` and then ``Content-Length: 5`` was read as a
    two-byte body, and whatever followed was parsed as the next request on
    the connection.

    RFC 7230 3.3.2 draws the line between duplicates that agree, which may
    be collapsed, and duplicates that disagree, which must be refused. A
    single field holding a comma list is treated the same way, since that
    is the other shape a client can use to send the same thing.
    """
    from .errors import SecurityError

    if values is None:
        return 0
    if isinstance(values, (str, bytes)):
        values = [values]
    parsed: list[int] = []
    for value in values:
        if isinstance(value, bytes):
            try:
                value = value.decode("latin-1")
            except UnicodeDecodeError:  # pragma: no cover - defensive
                raise FramingError("Content-Length must be ASCII digits") from None
        text = str(value)
        # A comma list is a #rule in RFC 7230 section 7, which permits
        # optional whitespace around the separators. Strip that here, and
        # nowhere else: a lone field value with stray whitespace is a
        # different question, and the header parser has already answered it.
        for part in (p.strip(" \t") for p in text.split(",")):
            try:
                parsed.append(parse_content_length(part, max_digits=max_digits))
            except SecurityError as e:
                raise FramingError(e.message) from e
    if not parsed:
        return 0
    first = parsed[0]
    for other in parsed[1:]:
        if other != first:
            raise FramingError(
                "request declares conflicting Content-Length values; "
                "message framing is ambiguous"
            )
    return first


def check_request_framing(headers: object) -> int:
    """Return the declared body length, refusing ambiguous framing.

    Checks the two rules that together define where a request body ends:
    a single resolvable Content-Length, and no Transfer-Encoding
    alongside it. ``Transfer-Encoding`` is not implemented and is never
    going to be, so the honest answer is to refuse rather than to read a
    zero-length body and let the chunks become a second request.

    Everything here raises ``FramingError`` rather than ``SecurityError``.
    The difference is what the server does next: a framing refusal means
    the body was never read, so the connection has to be closed, whereas
    a security refusal after a successful read leaves the connection
    perfectly usable.
    """

    def all_of(name: str) -> list[str]:
        getter = getattr(headers, "get_all", None)
        if getter is not None:
            return list(getter(name) or [])
        single = headers.get(name)  # type: ignore[attr-defined]
        return [] if single is None else [single]

    encodings = all_of("Transfer-Encoding")
    if encodings:
        raise FramingError(
            "Transfer-Encoding is not supported; MockRelay requires a "
            f"Content-Length (got {safe_repr(encodings)})"
        )
    return parse_content_length_fields(all_of("Content-Length"))


def parse_content_length(raw: object, *, max_digits: int = 18) -> int:
    """Return the declared body length, or 0 when no header was sent.

    Strict on purpose. A Content-Length is a promise about where the body
    ends, so anything outside a run of decimal digits is refused rather
    than interpreted. Python's ``int`` is far more permissive than HTTP:
    it takes a leading ``+``, ignores surrounding whitespace, and accepts
    underscore separators and non-ASCII digits. A negative value is worse
    than a parse failure, because ``rfile.read(-n)`` does not raise -- it
    reads to end of stream, so the request gets framed by whatever the
    client sends next.

    Raises SecurityError for every rejected shape.
    """
    from .errors import SecurityError

    if raw is None:
        return 0
    if isinstance(raw, bool):
        raise SecurityError("Content-Length must be a number, not a boolean")
    if isinstance(raw, int):
        if raw < 0:
            raise SecurityError("Content-Length must not be negative")
        return raw
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("ascii")
        except UnicodeDecodeError:
            raise SecurityError("Content-Length must be ASCII digits") from None
    text = str(raw)
    if not text:
        raise SecurityError("Content-Length was present but empty")
    if len(text) > max_digits:
        raise SecurityError(
            f"Content-Length has more than {max_digits} digits")
    for ch in text:
        if ch < "0" or ch > "9":
            bad = next(c for c in text if c < "0" or c > "9")
            raise SecurityError(
                "Content-Length must be a run of decimal digits, "
                f"got {safe_repr(text)!r} with {safe_repr(bad)!r}"
            )
    return int(text)


def sanitize_headers(
    pairs: Sequence[tuple[str, object]],
    max_headers: int = 100,
    max_total_bytes: int = 65536,
    drop_hop_by_hop: bool = True,
) -> tuple[list[tuple[str, str]], list[str]]:
    """Drop headers that cannot be sent safely, and enforce size limits.

    Returns the surviving pairs and a list of human-readable reasons. Reasons
    never include header values, because values may be credentials.
    """
    kept: list[tuple[str, str]] = []
    dropped: list[str] = []
    total = 0
    for name, value in pairs:
        key = str(name)
        if not is_valid_header_name(key):
            dropped.append(f"invalid header name {key!r}")
            continue
        if not is_valid_header_value(value):
            dropped.append(f"header {key} has an illegal value")
            continue
        if drop_hop_by_hop and key.lower() in HOP_BY_HOP_HEADERS:
            dropped.append(f"hop-by-hop header {key}")
            continue
        total += len(key) + len(str(value)) + 4
        if total > max_total_bytes:
            dropped.append("header block exceeds the configured limit")
            break
        if len(kept) >= max_headers:
            dropped.append("too many headers")
            break
        kept.append((key, str(value)))
    return kept, dropped


def ensure_writable_dir(path: Path, what: str = "directory") -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigError(
            [
                Problem(
                    f"cannot create the {what}: {exc.strerror or exc}",
                    location=str(path),
                )
            ],
            hint=f"Create it manually, or point {what} somewhere writable.",
        ) from exc
    if not os.access(str(path), os.W_OK | os.X_OK):
        raise ConfigError(
            [Problem(f"the {what} is not writable", location=str(path))],
            hint="Fix the permissions, or point the setting elsewhere.",
        )


def temporary_free_mb(path: Path) -> int | None:
    try:
        usage = os.statvfs(str(path))
    except (AttributeError, OSError):
        return None
    return int(usage.f_bavail * usage.f_frsize / (1024 * 1024))
