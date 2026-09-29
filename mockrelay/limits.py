"""Resource limits.

Every bound here exists because the input is untrusted: a developer proxy
forwards whatever a test suite or a local application sends it, and replay
loads files that may have been edited by hand or checked out from Git.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any

__all__ = ["DEFAULT_LIMITS", "Limits"]

KiB = 1024
MiB = 1024 * 1024


@dataclass(frozen=True)
class Limits:
    """Bounds applied to requests, responses, fixtures, and upstreams."""

    max_request_body: int = 10 * MiB
    max_response_body: int = 50 * MiB
    max_fixture_bytes: int = 16 * MiB
    max_config_bytes: int = 4 * MiB
    max_headers: int = 100
    max_header_bytes: int = 64 * KiB
    max_request_target: int = 8 * KiB
    max_query_pairs: int = 256
    max_path_segments: int = 64
    max_body_match_keys: int = 32
    max_redirects: int = 5
    upstream_timeout: float = 30.0
    connect_timeout: float = 10.0
    max_json_depth: int = 40

    def replace(self, **kw: Any) -> Limits:
        data = self.as_dict()
        data.update({k: v for k, v in kw.items() if k in data})
        return Limits(**data)

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def field_names(cls) -> tuple[str, ...]:
        return tuple(f.name for f in fields(cls))

    @classmethod
    def coerce(cls, raw: Mapping[str, Any]) -> tuple[Limits, list]:
        from .errors import Problem

        problems: list = []
        if not isinstance(raw, Mapping):
            return cls(), [
                Problem(
                    "must be a mapping of limit names to numbers",
                    subject="`limits`",
                    expected=", ".join(cls.field_names()),
                )
            ]
        values: dict[str, Any] = {}
        for key, value in raw.items():
            name = str(key)
            if name not in cls.field_names():
                problems.append(
                    Problem(
                        "is not a known limit",
                        subject=f"`{name}`",
                        expected=", ".join(cls.field_names()),
                    )
                )
                continue
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                problems.append(
                    Problem(
                        "must be a number",
                        subject=f"`{name}`",
                        expected="a positive number",
                    )
                )
                continue
            if value <= 0:
                problems.append(
                    Problem(
                        "must be greater than zero",
                        subject=f"`{name}`",
                        expected="a positive number",
                    )
                )
                continue
            if name.endswith("_timeout") and not 0 < float(value) <= 3600:
                problems.append(
                    Problem(
                        "must be between 0 and 3600 seconds",
                        subject=f"`{name}`",
                        expected="0 < seconds <= 3600",
                    )
                )
                continue
            values[name] = int(value) if not name.endswith("_timeout") else float(value)
        return cls(**values), problems


DEFAULT_LIMITS = Limits()
