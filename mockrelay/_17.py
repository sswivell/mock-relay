"""Fixture counting helpers for status output."""

from __future__ import annotations

import contextlib
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

from ._10 import _04 as _01


def _02(store: _01) -> dict[str, int]:
    counts: dict[str, int] = {}
    if not store.root.exists():
        return counts
    for d in sorted(store.root.iterdir()):
        if d.is_dir():
            counts[d.name] = sum(1 for _ in d.glob("*.json"))
    return counts


def _09(store: _01, upstream: str | None = None) -> list[dict[str, object]]:
    """Per-upstream totals: how much is recorded, and how old it is.

    Counts bytes because the reason to ask is usually "how big has this
    fixture set got", and tracks the recording window because the reason to
    ask that is usually "is any of this stale".
    """
    rows: dict[str, dict[str, object]] = {}
    for path, fx in store._12(upstream):
        row = rows.get(fx.upstream)
        if row is None:
            row = {
                "upstream": fx.upstream,
                "fixtures": 0,
                "bytes": 0,
                "methods": set(),
                "statuses": set(),
                "oldest": None,
                "newest": None,
            }
            rows[fx.upstream] = row
        row["fixtures"] = int(row["fixtures"]) + 1
        with contextlib.suppress(OSError):
            row["bytes"] = int(row["bytes"]) + path.stat().st_size
        row["methods"].add(str(fx.match.method).upper())  # type: ignore[union-attr]
        row["statuses"].add(int(fx.response.status))  # type: ignore[union-attr]
        when = fx.recorded_at
        if when:
            if row["oldest"] is None or when < row["oldest"]:  # type: ignore[operator]
                row["oldest"] = when
            if row["newest"] is None or when > row["newest"]:  # type: ignore[operator]
                row["newest"] = when
    out = []
    for name in sorted(rows):
        row = rows[name]
        row["methods"] = sorted(row["methods"])  # type: ignore[arg-type]
        row["statuses"] = sorted(row["statuses"])  # type: ignore[arg-type]
        out.append(row)
    return out


def _10(value: object) -> datetime | None:
    """Parse a recorded_at timestamp into an aware UTC datetime.

    Fixtures have been written by several versions of this tool, so the
    ISO 8601 shapes are accepted loosely rather than by one format string.
    """
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace(" ", "T", 1) if " " in value else value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _12(path: Path, recorded_at: object) -> datetime | None:
    """When a fixture was recorded, falling back to when the file was written.

    The fallback matters because a fixture written before timestamps were
    recorded at all is exactly the kind of thing a user wants pruned.
    """
    parsed = _10(recorded_at)
    if parsed is not None:
        return parsed
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None


def _11(
    store: _01,
    older_than_days: float,
    upstream: str | None = None,
    now: datetime | None = None,
) -> Iterator[tuple[Path, object]]:
    """Fixtures whose recorded time is older than the cutoff."""
    cutoff = (now or datetime.now(timezone.utc)).timestamp() - older_than_days * 86400
    for path, fx in store._12(upstream):
        when = _12(path, fx.recorded_at)
        if when is None:
            continue
        if when.timestamp() < cutoff:
            yield path, fx
