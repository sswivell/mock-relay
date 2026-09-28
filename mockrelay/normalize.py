"""Normalization of volatile values, so equivalent recordings diff cleanly.

Two recordings of the same call should produce the same fixture file. Anything
that changes between two otherwise identical calls goes through here first.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from re import Pattern
from typing import Any

__all__ = [
    "DEFAULT_VOLATILE_HEADERS",
    "DEFAULT_VOLATILE_KEYS",
    "NORMALIZED",
    "VOLATILE_VALUE_PATTERNS",
    "Normalizer",
    "apply_paths",
    "replace_paths",
]

NORMALIZED = "{{NORMALIZED}}"

DEFAULT_VOLATILE_HEADERS: tuple[str, ...] = (
    "date",
    "expires",
    "age",
    "last-modified",
    "x-request-id",
    "x-correlation-id",
    "x-request-id-generation",
    "x-amzn-trace-id",
    "x-amz-cf-id",
    "x-amz-cf-pop",
    "x-amzn-requestid",
    "traceparent",
    "tracestate",
    "b3",
    "x-b3-traceid",
    "x-b3-spanid",
    "x-timer",
    "server-timing",
    "cf-ray",
    "x-served-by",
    "x-cache",
    "x-cache-hits",
    "x-envoy-upstream-service-time",
)

DEFAULT_VOLATILE_KEYS: tuple[str, ...] = (
    "created",
    "created_at",
    "createdat",
    "updated",
    "updated_at",
    "modified",
    "modified_at",
    "last_modified",
    "timestamp",
    "time",
    "server_time",
    "request_id",
    "requestid",
    "request_guid",
    "trace_id",
    "traceid",
    "span_id",
    "spanid",
    "correlation_id",
    "nonce",
    "session_id",
    "elapsed",
    "duration_ms",
    "took_ms",
    "upstream_time",
)

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)
UUID_IN_TEXT = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I
)
ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?$"
)
ISO8601_IN_TEXT = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:?\d{2})?\b"
)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VOLATILE_VALUE_PATTERNS: tuple[tuple[str, Pattern[str], bool], ...] = (
    ("uuid", UUID_RE, True),
    ("timestamp", ISO8601_RE, True),
    ("date", DATE_RE, True),
    ("uuid-in-text", UUID_IN_TEXT, False),
    ("timestamp-in-text", ISO8601_IN_TEXT, False),
)

_EPOCH_FLOOR = 1_000_000_000
_MAX_DEPTH = 40


def _segments(path: str) -> list[str]:
    return [s for s in re.split(r"[.\[\]]+", path) if s]


def apply_paths(body: Any, paths: Sequence[str]) -> tuple[Any, list[str]]:
    """Replace the value at each dotted path with the placeholder.

    Returns the rewritten structure and the list of paths that were applied,
    so a caller can record what was normalized.
    """
    applied: list[str] = []
    for raw in paths:
        p = str(raw).strip()
        if p.startswith("$."):
            p = p[2:]
        if not p:
            continue
        if _replace(body, _segments(p), 0):
            applied.append(str(raw))
    return body, applied


def _replace(node: Any, keys: list[str], depth: int) -> bool:
    if not keys or depth > _MAX_DEPTH:
        return False
    key = keys[0]
    hit = False
    if isinstance(node, dict):
        if key in node:
            if len(keys) == 1:
                node[key] = NORMALIZED
                return True
            hit = _replace(node[key], keys[1:], depth + 1)
        else:
            for value in node.values():
                if isinstance(value, (dict, list)) and _replace(value, keys, depth + 1):
                    hit = True
    elif isinstance(node, list):
        for item in node:
            if _replace(item, keys, depth + 1):
                hit = True
    return hit


def replace_paths(body: Any, paths: Sequence[str]) -> Any:
    """In-place variant kept for callers that only need the result."""
    if not paths or not isinstance(body, (dict, list)):
        return body
    out, _ = apply_paths(body, paths)
    return out


def deep_copy(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: deep_copy(v) for k, v in value.items()}
    if isinstance(value, list):
        return [deep_copy(v) for v in value]
    if isinstance(value, tuple):
        return [deep_copy(v) for v in value]
    return value


@dataclass
class Normalizer:
    """Rewrites volatile values in recorded headers and JSON bodies."""

    json_paths: Sequence[str] = ()
    volatile_keys: Sequence[str] = DEFAULT_VOLATILE_KEYS
    volatile_headers: Sequence[str] = DEFAULT_VOLATILE_HEADERS
    value_patterns: Iterable[tuple[str, Pattern[str], bool]] = VOLATILE_VALUE_PATTERNS
    normalize_volatile: bool = True
    strip_volatile_headers: bool = True

    def __post_init__(self) -> None:
        self._keyset = {str(k).strip().lower() for k in (self.volatile_keys or ())}
        self._headerset = {
            str(h).strip().lower() for h in (self.volatile_headers or ())
        }
        self._patterns = tuple(self.value_patterns or ())

    def header_is_volatile(self, name: str) -> bool:
        return str(name).strip().lower() in self._headerset

    def headers(
        self, pairs: Sequence[tuple[str, str]]
    ) -> tuple[list[tuple[str, str]], list[str]]:
        kept: list[tuple[str, str]] = []
        removed: list[str] = []
        for name, value in pairs:
            if self.strip_volatile_headers and self.header_is_volatile(name):
                removed.append(str(name).lower())
                continue
            kept.append((str(name), value))
        return kept, removed

    def body(self, value: Any) -> tuple[Any, list[str]]:
        """Return a normalized copy of ``value`` and the fields changed."""
        if value is None:
            return None, []
        out = deep_copy(value)
        touched: list[str] = []
        if self.json_paths:
            _, applied = apply_paths(out, self.json_paths)
            touched.extend(applied)
        if self.normalize_volatile and self._patterns:
            self._walk(out, "$", touched, 0)
        return out, touched

    def _walk(self, node: Any, path: str, touched: list[str], depth: int) -> None:
        if depth > _MAX_DEPTH:
            return
        if isinstance(node, dict):
            for key, value in list(node.items()):
                child = f"{path}.{key}"
                if isinstance(value, (dict, list)):
                    self._walk(value, child, touched, depth + 1)
                    continue
                if str(key).strip().lower() in self._keyset and value is not None:
                    node[key] = NORMALIZED
                    touched.append(child)
                    continue
                if self._scrub(value, child, touched):
                    node[key] = NORMALIZED
                    touched.append(child)
        elif isinstance(node, list):
            for i, value in enumerate(node):
                child = f"{path}[{i}]"
                if isinstance(value, (dict, list)):
                    self._walk(value, child, touched, depth + 1)
                elif self._scrub(value, child, touched):
                    node[i] = NORMALIZED
                    touched.append(child)

    def _scrub(self, value: Any, path: str, touched: list[str]) -> bool:
        if isinstance(value, bool) or value is None:
            return False
        if isinstance(value, (int, float)):
            number = float(value)
            if number.is_integer() and abs(number) >= _EPOCH_FLOOR:
                touched.append(path)
                return True
            return False
        if not isinstance(value, str):
            return False
        for _name, rx, whole in self._patterns:
            hit = rx.match(value) if whole else rx.search(value)
            if hit and (whole or hit.group(0) != value):
                touched.append(path)
                return True
        return False

    def text(self, value: str) -> tuple[str, list[str]]:
        """Replace volatile values embedded in a non-JSON string."""
        if not isinstance(value, str) or not value or not self.normalize_volatile:
            return value, []
        touched: list[str] = []
        out = value
        for _name, rx, whole in self._patterns:
            if whole:
                if rx.match(out):
                    out = NORMALIZED
                    touched.append("$text")
            else:
                out, n = rx.subn(NORMALIZED, out)
                if n:
                    touched.append("$text")
        return out, touched


def default_normalizer(
    json_paths: Sequence[str] | None = None,
    normalize_volatile: bool = True,
) -> Normalizer:
    return Normalizer(
        json_paths=list(json_paths or ()), normalize_volatile=normalize_volatile
    )
