"""Fixture statistics and pruning, which the store has to support directly.

Both commands have to know where a fixture lives on disk, because one
counts bytes and the other deletes files. Reading the tree by hand in the
CLI would walk past the store's path handling, so the store grows a
reader that yields the path alongside the parsed fixture and the existing
reader is expressed in terms of it.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

import pytest

from mockrelay._10 import _04 as Store
from mockrelay._17 import _09 as _stats


def _record(
    store, upstream, fixture_id, path="/x", status=200, recorded_at=None, body=None
):
    from mockrelay._06 import _01 as Match
    from mockrelay._06 import _04 as Request
    from mockrelay._06 import _05 as Response
    from mockrelay._06 import _06 as Fixture

    fx = Fixture(
        id=fixture_id,
        upstream=upstream,
        match=Match(method="GET", path=path),
        request=Request(method="GET", path=path),
        response=Response(status=status, body=body or {"ok": True}),
        recorded_at=recorded_at,
    )
    return store._06(upstream, fx)


def test_01_the_store_yields_a_path_beside_each_fixture(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    rows = list(store._12())
    assert len(rows) == 1
    path, fx = rows[0]
    assert path.exists()
    assert path.name == "a.json"
    assert fx.id == "a"


def test_02_the_plain_reader_is_the_path_reader_without_the_path(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    _record(store, "gh", "b")
    assert [f.id for f in store._07()] == [f.id for _, f in store._12()]


def test_03_an_unreadable_fixture_is_recorded_by_both_readers(tmp_path):
    store = Store(tmp_path)
    bad = tmp_path / "gh" / "bad.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("{not json", encoding="utf-8")
    assert list(store._12()) == []
    assert store.problems
    assert list(store._07()) == []
    assert store.problems


def test_04_the_path_reader_honours_the_upstream_filter(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    _record(store, "stripe", "b")
    assert [fx.upstream for _, fx in store._12("gh")] == ["gh"]


def test_05_statistics_are_grouped_by_upstream(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    _record(store, "gh", "b")
    _record(store, "stripe", "c")
    rows = {r["upstream"]: r for r in _stats(store)}
    assert rows["gh"]["fixtures"] == 2
    assert rows["stripe"]["fixtures"] == 1


def test_06_statistics_count_bytes_on_disk(tmp_path):
    store = Store(tmp_path)
    path = _record(store, "gh", "a")
    rows = _stats(store)
    assert rows[0]["bytes"] == path.stat().st_size


def test_07_statistics_collect_methods_and_statuses(tmp_path):
    from mockrelay._06 import _01 as Match
    from mockrelay._06 import _04 as Request
    from mockrelay._06 import _05 as Response
    from mockrelay._06 import _06 as Fixture

    store = Store(tmp_path)
    store._06(
        "gh",
        Fixture(
            id="post",
            upstream="gh",
            match=Match(method="POST", path="/x"),
            request=Request(method="POST", path="/x"),
            response=Response(status=201),
            recorded_at=None,
        ),
    )
    _record(store, "gh", "get", status=404)
    row = _stats(store)[0]
    assert row["methods"] == ["GET", "POST"]
    assert row["statuses"] == [201, 404]


def test_08_statistics_report_the_recording_window(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "old", recorded_at="2024-01-01T00:00:00Z")
    _record(store, "gh", "new", recorded_at="2024-06-01T00:00:00Z")
    row = _stats(store)[0]
    assert row["oldest"] == "2024-01-01T00:00:00Z"
    assert row["newest"] == "2024-06-01T00:00:00Z"


def _strip_timestamp(path):
    """Remove recorded_at, the way a hand-written fixture may not have it."""
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["recorded_at"] = None
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_09_statistics_tolerate_a_fixture_with_no_timestamp(tmp_path):
    store = Store(tmp_path)
    _strip_timestamp(_record(store, "gh", "a"))
    row = _stats(store)[0]
    assert row["oldest"] is None
    assert row["newest"] is None
    assert row["fixtures"] == 1


def test_10_statistics_are_empty_for_an_empty_store(tmp_path):
    assert _stats(Store(tmp_path)) == []


def test_11_statistics_can_be_limited_to_one_upstream(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    _record(store, "stripe", "b")
    rows = _stats(store, "gh")
    assert [r["upstream"] for r in rows] == ["gh"]


def test_12_statistics_ignore_unreadable_files_but_still_report(tmp_path):
    store = Store(tmp_path)
    _record(store, "gh", "a")
    bad = tmp_path / "gh" / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    rows = _stats(store)
    assert rows[0]["fixtures"] == 1
    assert store.problems


@pytest.mark.parametrize(
    "text",
    [
        "2024-01-01T00:00:00Z",
        "2024-01-01T00:00:00+00:00",
        "2024-01-01T00:00:00.500Z",
        "2024-01-01 00:00:00",
        "2024-01-01T00:00:00",
    ],
)
def test_13_recorded_at_is_parsed(text):
    from mockrelay._17 import _10 as _when

    assert _when(text) is not None


@pytest.mark.parametrize("text", [None, "", "yesterday", 12, "2024-13-45T99:99:99Z"])
def test_14_an_unparseable_timestamp_is_none(text):
    from mockrelay._17 import _10 as _when

    assert _when(text) is None


def test_15_a_naive_timestamp_is_assumed_utc():
    from mockrelay._17 import _10 as _when

    got = _when("2024-01-01T00:00:00Z")
    assert got.tzinfo is not None
    assert got == datetime(2024, 1, 1, tzinfo=timezone.utc)


def test_16_old_fixtures_are_selected_for_removal(tmp_path):
    from mockrelay._17 import _11 as _stale

    store = Store(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    _record(store, "gh", "old", recorded_at=old)
    _record(store, "gh", "new")
    picked = list(_stale(store, older_than_days=30))
    assert [path.name for path, _ in picked] == ["old.json"]


def test_17_a_fixture_with_no_timestamp_falls_back_to_the_file_mtime(tmp_path):
    import os

    from mockrelay._17 import _11 as _stale

    store = Store(tmp_path)
    path = _strip_timestamp(_record(store, "gh", "a"))
    long_ago = time.time() - 90 * 86400
    os.utime(path, (long_ago, long_ago))
    picked = list(_stale(store, older_than_days=30))
    assert [p.name for p, _ in picked] == ["a.json"]


def test_18_recent_fixtures_are_kept(tmp_path):
    from mockrelay._17 import _11 as _stale

    store = Store(tmp_path)
    _record(store, "gh", "a")
    assert list(_stale(store, older_than_days=30)) == []


def test_19_the_stale_reader_honours_the_upstream_filter(tmp_path):
    from mockrelay._17 import _11 as _stale

    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    store = Store(tmp_path)
    _record(store, "gh", "a", recorded_at=old)
    _record(store, "stripe", "b", recorded_at=old)
    picked = list(_stale(store, older_than_days=30, upstream="gh"))
    assert [fx.upstream for _, fx in picked] == ["gh"]
