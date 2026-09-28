"""Fixture store: content-addressed JSON files under fixtures_dir, with ids and listing."""
from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ._06 import _01 as _01
from ._06 import _06 as _02
from .security import ensure_writable_dir, safe_child, validate_component

MAX_REPORTED_PROBLEMS = 100


def _03(upstream: str, match: _01) -> str:
    payload: dict[str, Any] = {
        "u": upstream,
        "m": match.method.upper(),
        "p": match.path,
        "q": {k: sorted(v) for k, v in sorted(match.query_subset.items())},
        "b": match.body_contains,
    }
    mode = getattr(match, "match_mode", None)
    if mode:
        payload["mm"] = mode
    prio = getattr(match, "priority", None)
    if prio:
        payload["pr"] = prio
    # SHA-1 here is a content fingerprint for a stable fixture id, never a
    # security primitive: preimage resistance is not what the id depends on,
    # and switching the algorithm would re-key every recorded fixture.
    return hashlib.sha1(  # noqa: S324
        json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:12]


@dataclass(frozen=True)
class _31:
    """A fixture file that could not be read back.

    Recorded rather than swallowed, because a fixture that silently fails
    to load turns into a 501 "no fixture matched" with no explanation.
    """

    path: str
    reason: str

    def render(self) -> str:
        return f"{self.path}: {self.reason}"


class _04:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.problems: list[_31] = []
        self.problem_count = 0

    def _05(self, upstream: str, fixture_id: str) -> Path:
        target = safe_child(self.root, str(upstream), f"{fixture_id}.json")
        validate_component(fixture_id, "fixture id")
        ensure_writable_dir(target.parent, "fixture directory")
        return target

    def _06(self, upstream: str, fixture: _02) -> Path:
        p = self._05(upstream, fixture.id)
        fixture.recorded_at = fixture.recorded_at or time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        tmp = p.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(fixture._07(), indent=2), encoding="utf-8")
        # Rename over the target so a crash mid-write cannot leave a
        # half-written fixture where a complete one used to be.
        tmp.replace(p)
        return p

    def _10(self, path: Path, exc: Exception) -> None:
        self.problem_count += 1
        if len(self.problems) < MAX_REPORTED_PROBLEMS:
            self.problems.append(_31(str(path), type(exc).__name__))

    def _11(self) -> list[str]:
        """Human-readable summary of what _07 skipped, for CLI reporting."""
        out = [p.render() for p in self.problems]
        hidden = self.problem_count - len(self.problems)
        if hidden > 0:
            out.append(f"... and {hidden} more unreadable fixture file(s)")
        return out

    def _07(self, upstream: str | None = None) -> Iterator[_02]:
        self.problems = []
        self.problem_count = 0
        search = safe_child(self.root, str(upstream)) if upstream else self.root
        if not search.exists():
            return
        for path in sorted(search.rglob("*.json")):
            try:
                yield _02._08(json.loads(path.read_text()))
            except (OSError, ValueError, KeyError, TypeError) as e:
                self._10(path, e)

    def _08(self, upstream: str, fixture_id: str) -> bool:
        p = self._05(upstream, fixture_id)
        if p.exists():
            p.unlink()
            return True
        return False

    @staticmethod
    def _09(upstream: str, match: _01) -> str:
        return f"{upstream}-{match.method.lower()}-{_03(upstream, match)}"
