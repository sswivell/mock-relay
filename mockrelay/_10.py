"""Fixture store: content-addressed JSON files under fixtures_dir, with ids and listing."""
from __future__ import annotations
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from ._06 import _01 as _01
from ._06 import _06 as _02
from .security import ensure_writable_dir, safe_child, validate_component


def _03(upstream: str, match: _01) -> str:
    payload: Dict[str, Any] = {
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
    return hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:12]


class _04:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

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
        tmp.write_text(json.dumps(fixture._07(), indent=2))
        os.replace(tmp, p)
        return p

    def _07(self, upstream: Optional[str] = None) -> Iterator[_02]:
        search = safe_child(self.root, str(upstream)) if upstream else self.root
        if not search.exists():
            return
        for path in sorted(search.rglob("*.json")):
            try:
                yield _02._08(json.loads(path.read_text()))
            except Exception:
                continue

    def _08(self, upstream: str, fixture_id: str) -> bool:
        p = self._05(upstream, fixture_id)
        if p.exists():
            p.unlink()
            return True
        return False

    @staticmethod
    def _09(upstream: str, match: _01) -> str:
        return f"{upstream}-{match.method.lower()}-{_03(upstream, match)}"
