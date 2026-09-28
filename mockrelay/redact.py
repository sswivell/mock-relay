"""Secret detection and redaction.

Redaction runs before anything is written to disk, and again on anything that
is logged, exported, or reported to a user. It is a best-effort filter, not a
guarantee: the patterns here catch the credential shapes that appear in
practice, and no pattern list can be complete. Review fixtures before
committing them.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, unquote_plus

__all__ = [
    "DEFAULT_REDACT_BODY_KEYS",
    "DEFAULT_REDACT_HEADERS",
    "DEFAULT_REDACT_JSON_PATHS",
    "NORMALIZED",
    "PLACEHOLDERS",
    "REDACTED",
    "SECRET_PATTERNS",
    "Finding",
    "Redactor",
    "is_placeholder",
    "scrub",
]

REDACTED = "{{SECRET}}"
NORMALIZED = "{{NORMALIZED}}"
PLACEHOLDERS = (REDACTED, NORMALIZED)

AUTH_HEADER_NAMES = frozenset(
    (
        "authorization",
        "proxy_authorization",
        "www_authenticate",
        "proxy_authenticate",
        "authentication",
    )
)

DEFAULT_REDACT_HEADERS: tuple[str, ...] = (
    "authorization",
    "proxy-authorization",
    "cookie",
    "set-cookie",
    "set-cookie2",
    "x-api-key",
    "api-key",
    "apikey",
    "x-auth-token",
    "x-access-token",
    "x-session-token",
    "x-csrf-token",
    "x-xsrf-token",
    "x-amz-security-token",
    "x-goog-api-key",
    "x-client-secret",
    "x-hub-signature",
    "x-hub-signature-256",
    "stripe-secret-key",
    "private-token",
    "authentication",
)

DEFAULT_REDACT_BODY_KEYS: tuple[str, ...] = (
    "password",
    "passwd",
    "pwd",
    "pass",
    "secret",
    "client_secret",
    "consumer_secret",
    "app_secret",
    "token",
    "access_token",
    "refresh_token",
    "id_token",
    "bearer_token",
    "auth_token",
    "session_token",
    "session_id",
    "sessionid",
    "jwt",
    "api_key",
    "apikey",
    "api_secret",
    "access_key",
    "secret_key",
    "private_key",
    "privatekey",
    "passphrase",
    "credentials",
    "aws_secret_access_key",
    "aws_session_token",
    "aws_access_key_id",
    "authorization",
    "auth",
    "signature",
    "otp",
    "totp",
    "credit_card",
    "card_number",
    "cvv",
    "cvc",
)

DEFAULT_REDACT_JSON_PATHS: tuple[str, ...] = (
    "$.password",
    "$.token",
    "$.access_token",
    "$.refresh_token",
    "$.id_token",
    "$.client_secret",
    "$.api_key",
    "$.secret",
    "$.credentials.*",
)

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private-key",
        re.compile(
            r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?"
            r"-----END (?:[A-Z ]+ )?PRIVATE KEY-----"
        ),
    ),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}"
            r"(?:\.[A-Za-z0-9_-]*)?"
        ),
    ),
    (
        "bearer",
        re.compile(r"(?i)\b(bearer|token|secret|basic)\s+([A-Za-z0-9\-._~+/]{8,}=*)"),
    ),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b")),
    (
        "aws-secret",
        re.compile(
            r"(?i)\baws_secret_access_key\b(\s*[=:]\s*)[\"']?"
            r"([A-Za-z0-9/+=]{40})"
        ),
    ),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("google-oauth", re.compile(r"\bya29\.[0-9A-Za-z_\-]{20,}\b")),
    (
        "github",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{16,}|github_pat_[A-Za-z0-9_]{20,})"),
    ),
    ("gitlab", re.compile(r"\bglpat-[A-Za-z0-9_\-]{16,}\b")),
    ("stripe", re.compile(r"\b[srp]k_(?:live|test)_[A-Za-z0-9]{6,}\b")),
    ("slack", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    (
        "slack-webhook",
        re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/+_=-]{20,}"),
    ),
    ("sendgrid", re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b")),
    ("twilio", re.compile(r"\bSK[0-9a-fA-F]{32}\b")),
    ("npm", re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b")),
    ("digitalocean", re.compile(r"\bdo[oprv]_[a-f0-9]{64}\b")),
    ("openai", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b")),
    ("database-url", re.compile(r"(?i)\b(://)[^\s:/@]+:[^\s@/]+@")),
    (
        "url-secret",
        re.compile(
            r"(?i)([?&](?:access_token|token|api_key|apikey|key|secret|password|"
            r"pwd|auth|signature|sig|client_secret|session|sessionid|"
            r"auth_token|refresh_token)=)[^&#\s\"']+"
        ),
    ),
    (
        "form-secret",
        re.compile(
            r"(?i)\b(password|passwd|pwd|token|access_token|refresh_token|"
            r"api_key|apikey|client_secret|secret|auth|authorization|"
            r"session|sessionid|signature)=([^&\s\"';]{1,})"
        ),
    ),
    (
        "assignment-secret",
        re.compile(
            r"(?i)([\"']?(?:password|passwd|pwd|client_secret|api_secret|"
            r"secret_key|access_token|refresh_token|api_key|apikey|"
            r"private_key|passphrase)[\"']?\s*[:=]\s*)"
            r"[\"'][^\"']{1,}[\"']"
        ),
    ),
)

_KEY_SPLIT = re.compile(r"[.\[\]]+")
_MAX_DEPTH = 40
_MAX_NODES = 200000


@dataclass(frozen=True)
class Finding:
    """A location a secret was seen. Never carries the secret itself."""

    location: str
    kind: str

    def as_dict(self) -> dict[str, str]:
        return {"location": self.location, "kind": self.kind}


@dataclass
class _Walk:
    findings: list[Finding] = field(default_factory=list)
    seen: int = 0

    def note(self, location: str, kind: str) -> None:
        self.findings.append(Finding(location, kind))


def is_placeholder(value: Any) -> bool:
    return isinstance(value, str) and value in PLACEHOLDERS


def _norm_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def _replacement_for(name: str) -> str:
    if name == "bearer":
        return r"\1 " + REDACTED
    if name == "aws-secret":
        return r"\1" + REDACTED
    if name == "database-url":
        return r"\1" + REDACTED + "@"
    if name == "url-secret":
        return r"\1" + REDACTED
    if name == "form-secret":
        return r"\1=" + REDACTED
    if name == "assignment-secret":
        return r'\1"' + REDACTED + '"'
    return REDACTED


def _apply_patterns(text: str, walk: _Walk, location: str, report_only: bool) -> str:
    out = text
    for name, rx in SECRET_PATTERNS:
        if not rx.search(out):
            continue
        walk.note(location, name)
        if not report_only:
            out = rx.sub(_replacement_for(name), out)
    return out


def scrub(text: Any) -> str:
    """Redact secret-looking substrings in a flat string."""
    if not isinstance(text, str) or not text:
        return ""
    walk = _Walk()
    return _apply_patterns(text, walk, "", False)


def _looks_secret(name: str, extra: Iterable[str]) -> bool:
    if name in extra:
        return True
    if name in AUTH_HEADER_NAMES:
        return True
    for suffix in (
        "_key",
        "_token",
        "_secret",
        "_password",
        "_credential",
        "_credentials",
        "_signature",
    ):
        if name.endswith(suffix):
            return True
    return False


def _path_matchers(paths: Sequence[str]) -> list[list[str]]:
    out: list[list[str]] = []
    for raw in paths:
        p = str(raw).strip()
        if p == "$":
            continue
        if p.startswith("$."):
            p = p[2:]
        parts = [seg for seg in _KEY_SPLIT.split(p) if seg]
        if parts:
            out.append([seg.lower() for seg in parts])
    return out


def _path_matches(segments: Sequence[str], matchers: Sequence[Sequence[str]]) -> bool:
    for parts in matchers:
        if len(parts) != len(segments):
            continue
        if all(
            p == s
            or (
                ("*" in p or "?" in p)
                and re.match(
                    "^" + re.escape(p).replace(r"\*", ".*").replace(r"\?", ".") + "$", s
                )
            )
            for p, s in zip(parts, segments, strict=True)
        ):
            return True
    return False


class Redactor:
    """Configurable redaction of headers, bodies, paths, and free text."""

    def __init__(
        self,
        headers: Iterable[str] | None = None,
        body_keys: Iterable[str] | None = None,
        json_paths: Iterable[str] | None = None,
        extra_patterns: Iterable[str] | None = None,
        enabled: bool = True,
    ) -> None:
        self.enabled = bool(enabled)
        self.header_names = {
            _norm_key(h)
            for h in (headers if headers is not None else DEFAULT_REDACT_HEADERS)
        }
        self.body_keys = {
            _norm_key(k)
            for k in (body_keys if body_keys is not None else DEFAULT_REDACT_BODY_KEYS)
        }
        self.json_paths = list(
            json_paths if json_paths is not None else DEFAULT_REDACT_JSON_PATHS
        )
        self.extra_patterns = tuple(
            (f"custom-{i}", re.compile(p)) for i, p in enumerate(extra_patterns or ())
        )
        self._matchers = _path_matchers(self.json_paths)
        self.all_patterns = SECRET_PATTERNS + self.extra_patterns

    def describe(self) -> dict[str, list[str]]:
        return {
            "headers": sorted(self.header_names),
            "body_keys": sorted(self.body_keys),
            "json_paths": list(self.json_paths),
        }

    def header_names_match(self, name: str) -> bool:
        return _norm_key(name) in self.header_names

    def headers(
        self, pairs: Sequence[tuple[str, str]]
    ) -> tuple[list[tuple[str, str]], list[Finding]]:
        walk = _Walk()
        out: list[tuple[str, str]] = []
        for name, value in pairs:
            key = str(name)
            loc = "header:" + key
            if self.enabled and self.header_names_match(key):
                walk.note(loc, "sensitive-header")
                out.append((key, REDACTED))
                continue
            if not isinstance(value, str):
                out.append((key, value))
                continue
            cleaned = _apply_patterns(value, walk, loc, not self.enabled)
            if self.enabled and _norm_key(key) in AUTH_HEADER_NAMES:
                out.append((key, REDACTED))
            else:
                out.append((key, cleaned))
        return out, walk.findings

    def text(self, value: str, location: str = "") -> tuple[str, list[Finding]]:
        if not isinstance(value, str) or not value:
            return (value if isinstance(value, str) else ""), []
        walk = _Walk()
        return _apply_patterns(value, walk, location, not self.enabled), walk.findings

    def value(self, value: Any, location: str = "$") -> tuple[Any, list[Finding]]:
        walk = _Walk()
        out = self._node(value, location, walk, 0)
        return out, walk.findings

    def audit(self, value: Any, location: str = "$") -> list[Finding]:
        return self.value(value, location)[1]

    def _node(self, node: Any, path: str, walk: _Walk, depth: int) -> Any:
        if depth > _MAX_DEPTH:
            walk.note(path, "depth-limit")
            return node
        walk.seen += 1
        if walk.seen > _MAX_NODES:
            walk.note(path, "node-limit")
            return node
        if isinstance(node, dict):
            return {k: self._child(k, v, path, walk, depth) for k, v in node.items()}
        if isinstance(node, (list, tuple)):
            return [
                self._child(f"[{i}]", v, path, walk, depth) for i, v in enumerate(node)
            ]
        if isinstance(node, str):
            return _apply_patterns(node, walk, path, not self.enabled)
        return node

    def _child(self, key: Any, node: Any, path: str, walk: _Walk, depth: int) -> Any:
        label = str(key)
        child_path = path + label if label.startswith("[") else f"{path}.{label}"
        if self.enabled:
            segments = [seg for seg in _KEY_SPLIT.split(child_path) if seg]
            if _looks_secret(_norm_key(label), self.body_keys) or _path_matches(
                segments, self._matchers
            ):
                walk.note(child_path, "sensitive-field")
                return REDACTED
        return self._node(node, child_path, walk, depth + 1)

    def query(
        self, query: dict[str, list[str]]
    ) -> tuple[dict[str, list[str]], list[Finding]]:
        walk = _Walk()
        out: dict[str, list[str]] = {}
        for key, values in (query or {}).items():
            loc = "query:" + str(key)
            if self.enabled and _looks_secret(_norm_key(key), self.body_keys):
                walk.note(loc, "sensitive-query")
                out[key] = [REDACTED for _ in (values or [""])]
                continue
            new_values: list[Any] = []
            for v in values or []:
                if isinstance(v, str) and self.enabled:
                    new_values.append(_apply_patterns(v, walk, loc, False))
                else:
                    new_values.append(v)
            out[key] = new_values
        return out, walk.findings

    def request_target(
        self, path: str, query_string: str
    ) -> tuple[str, str, list[Finding]]:
        """Redact a path and a raw query string in place, keeping them usable.

        The query string is re-encoded, so percent-escaping is normalised. That
        is intentional: it is the only way to redact a value that may itself
        contain an ``&``.
        """
        walk = _Walk()
        clean_path = _apply_patterns(path, walk, "path", not self.enabled)
        out_query = ""
        for part in (query_string or "").split("&"):
            if not part:
                continue
            raw_key, _, raw_value = part.partition("=")
            key = unquote_plus(raw_key)
            value = unquote_plus(raw_value)
            if self.enabled and _looks_secret(_norm_key(key), self.body_keys):
                walk.note("query:" + key, "sensitive-query")
                out_query += (
                    "&" if out_query else ""
                ) + f"{quote(raw_key, safe='')}={quote(REDACTED, safe='')}"
                continue
            clean = _apply_patterns(value, walk, "query:" + key, not self.enabled)
            out_query += (
                "&" if out_query else ""
            ) + f"{quote(raw_key, safe='')}={quote(clean, safe='')}"
        return clean_path, out_query, walk.findings
