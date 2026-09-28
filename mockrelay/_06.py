"""Data classes for match specs, requests, responses, and fixtures."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class _01:
    method: str
    path: str
    query_subset: dict[str, list[str]] = field(default_factory=dict)
    body_contains: dict[str, Any] | None = None
    match_mode: str | None = None
    fuzzy_threshold: float | None = None
    ignore_case: bool | None = None
    priority: int | None = None

    def _02(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def _03(cls, d: dict[str, Any]) -> _01:
        prio = d.get("priority")
        if prio is not None:
            try:
                prio = int(prio)
            except (TypeError, ValueError):
                prio = None
        return cls(
            method=d["method"],
            path=d["path"],
            query_subset=d.get("query_subset") or {},
            body_contains=d.get("body_contains"),
            match_mode=d.get("match_mode"),
            fuzzy_threshold=d.get("fuzzy_threshold"),
            ignore_case=d.get("ignore_case"),
            priority=prio,
        )


@dataclass
class _04:
    method: str
    path: str
    query: dict[str, list[str]] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


@dataclass
class _05:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    body: Any = None


@dataclass
class _06:
    id: str
    upstream: str
    match: _01
    request: _04
    response: _05
    normalize: list[str] = field(default_factory=list)
    recorded_at: str | None = None
    call_index: int = 0

    def _07(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "upstream": self.upstream,
            "match": self.match._02(),
            "request": asdict(self.request),
            "response": asdict(self.response),
            "normalize": self.normalize,
            "recorded_at": self.recorded_at,
            "call_index": self.call_index,
        }

    @classmethod
    def _08(cls, d: dict[str, Any]) -> _06:
        return cls(
            id=d["id"],
            upstream=d["upstream"],
            match=_01._03(d["match"]),
            request=_04(**d["request"]),
            response=_05(**d["response"]),
            normalize=d.get("normalize") or [],
            recorded_at=d.get("recorded_at"),
            call_index=d.get("call_index", 0),
        )
