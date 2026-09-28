"""Tests for reporting fixtures the store could not read back.

`_07` used to catch bare `Exception` and `continue`, so a truncated file,
a hand-edited fixture missing `response`, or an unreadable permission bit
all disappeared. A replay miss then surfaced as a 501 "no fixture
matched" with nothing pointing at the broken file.
"""

import json
import os
import sys

import pytest

from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import MAX_REPORTED_PROBLEMS
from mockrelay._10 import _04 as Store

needs_posix_bits = pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows does not enforce POSIX permission bits")


def _fx(fid, path="/users/7"):
    return _06(id=fid, upstream="u",
               match=_01(method="GET", path=path),
               request=_04(method="GET", path=path),
               response=_05(status=200, body={"ok": True}))


def _broken(store, name, text="{"):
    d = store.root / "u"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(text, encoding="utf-8")


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path)


def test_reads_back_a_well_formed_fixture(store):
    store._06("u", _fx("good"))
    assert [f.id for f in store._07()] == ["good"]
    assert store.problems == []
    assert store._11() == []


def test_truncated_json_is_reported_not_swallowed(store):
    _broken(store, "broken.json", '{"id": "broke')
    assert list(store._07()) == []
    assert store.problem_count == 1
    rendered = store._11()[0]
    assert "broken.json" in rendered
    assert "JSONDecodeError" in rendered


def test_missing_required_key_is_reported(store):
    """A syntactically valid file that is not a fixture shape."""
    _broken(store, "shape.json", json.dumps({"id": "x"}))
    assert list(store._07()) == []
    assert store.problem_count == 1
    assert store._11()[0].endswith("KeyError")


def test_wrong_shape_is_reported(store):
    """A JSON document where a fixture object was expected."""
    _broken(store, "list.json", json.dumps([1, 2, 3]))
    assert list(store._07()) == []
    assert store.problem_count == 1


def test_good_fixtures_survive_alongside_broken_ones(store):
    store._06("u", _fx("aaa"))
    store._06("u", _fx("zzz"))
    _broken(store, "broken.json", "not json at all")
    assert [f.id for f in store._07()] == ["aaa", "zzz"]
    assert store.problem_count == 1


def test_problem_list_is_bounded_but_the_count_is_not(store):
    extra = 25
    for i in range(MAX_REPORTED_PROBLEMS + extra):
        _broken(store, f"bad{i:04d}.json")
    assert list(store._07()) == []
    assert store.problem_count == MAX_REPORTED_PROBLEMS + extra
    assert len(store.problems) == MAX_REPORTED_PROBLEMS
    assert f"and {extra} more unreadable fixture file(s)" in store._11()[-1]


def test_problems_reset_between_listings(store):
    store._06("u", _fx("ok"))
    _broken(store, "broken.json")
    list(store._07())
    assert store.problem_count == 1
    (store.root / "u" / "broken.json").unlink()
    assert [f.id for f in store._07()] == ["ok"]
    assert store.problems == []
    assert store.problem_count == 0


def test_problems_are_scoped_to_the_listed_upstream(store):
    """Reading a clean upstream must not report another one's damage."""
    store._06("u", _fx("good"))
    _broken(store, "broken.json")
    list(store._07("u"))
    assert store.problem_count == 1
    store._06("v", _fx("other"))
    assert [f.id for f in store._07("v")] == ["other"]
    assert store.problem_count == 0
    assert store._11() == []


def test_a_genuine_bug_is_not_swallowed(store, monkeypatch):
    """The old bare `except Exception` also hid bugs and SecurityError."""

    def boom(raw):
        raise RuntimeError("a genuine bug, not bad data")

    _broken(store, "x.json", json.dumps({"id": "x"}))
    monkeypatch.setattr(_06, "_08", staticmethod(boom))
    with pytest.raises(RuntimeError, match="genuine bug"):
        list(store._07())
    assert store.problem_count == 0


@needs_posix_bits
def test_unreadable_file_is_reported(store):
    store._06("u", _fx("ok"))
    locked = store.root / "u" / "locked.json"
    locked.write_text(json.dumps(_fx("x")._07()), encoding="utf-8")
    locked.chmod(0o000)
    try:
        ids = [f.id for f in store._07()]
    finally:
        locked.chmod(0o600)
    if os.geteuid() == 0:
        assert ids == ["ok", "x"]  # root ignores the mode bits
        return
    assert ids == ["ok"]
    assert store.problem_count == 1
    assert "locked.json" in store._11()[0]
