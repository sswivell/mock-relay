"""Regression tests for fixture-store path traversal.

The upstream name reaches the store straight from the request target
(`/<upstream>/<path>`) and from the admin API's query string, so it is
fully attacker-controlled. Before the store validated its path
components, `DELETE /api/fixtures/../important` deleted a file next to the
fixtures directory and `GET /api/fixtures?upstream=..` read any *.json
above it.
"""

import json
import tempfile
from pathlib import Path

import pytest

from mockrelay._06 import _01, _04, _05, _06
from mockrelay._10 import _04 as Store
from mockrelay.errors import SecurityError

TRAVERSAL_UPSTREAMS = [
    "..",
    "../..",
    "....",
    "..\\..",
    "../fixtures",
    "a/../../b",
    "a\\..\\..\\b",
    "./..",
    "gh/../..",
    "..%2f..",
    "\u202e..",
    "/etc",
    "C:\\Windows",
    "\\\\server\\share",
    "gh\u0000..",
    ".. ",
]


def _store(root: Path) -> Store:
    return Store(root)


def _fixture(fid: str = "f1") -> _06:
    return _06(id=fid, upstream="u", match=_01(method="GET", path="/x"),
               request=_04(method="GET", path="/x"),
               response=_05(status=200, body={"ok": True}))


def test_01_path_never_escapes_the_fixtures_root():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "fixtures"
        s = _store(root)
        resolved_root = root.resolve()
        for bad in TRAVERSAL_UPSTREAMS:
            with pytest.raises(SecurityError):
                s._05(bad, "f1")
        with pytest.raises(SecurityError):
            s._05("u", "../f1")
        assert resolved_root.is_dir()


def test_02_delete_cannot_reach_a_file_outside_the_root():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        root = base / "fixtures"
        root.mkdir()
        victim = base / "important.json"
        victim.write_text('{"keep":true}')
        s = _store(root)
        for bad in ("..", "../..", "a/.."):
            with pytest.raises(SecurityError):
                s._08(bad, "important")
        assert victim.exists(), "a file outside the fixtures dir was deleted"


def test_03_listing_cannot_escape_the_root():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        root = base / "fixtures"
        root.mkdir()
        (base / "elsewhere").mkdir()
        (base / "elsewhere" / "leak.json").write_text('{"id":"leak"}')
        s = _store(root)
        for bad in ("..", "../elsewhere", "..\\elsewhere"):
            with pytest.raises(SecurityError):
                list(s._07(bad))
        assert list(s._07("u")) == []


def test_04_write_cannot_escape_the_root():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        root = base / "fixtures"
        root.mkdir()
        s = _store(root)
        for bad in ("..", "../.."):
            with pytest.raises(SecurityError):
                s._06(bad, _fixture())
        assert not (base / "f1.json").exists()
        assert sorted(p.name for p in base.iterdir()) == ["fixtures"]


def test_05_a_symlinked_upstream_cannot_redirect_writes_outside(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "fixtures"
    (root / "real").mkdir(parents=True)
    link = root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("symlinks are not available to this user")
    s = Store(root)
    with pytest.raises(SecurityError):
        s._06("escape", _fixture())
    assert not (outside / "f1.json").exists()


def test_06_ordinary_upstream_names_still_work():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "fixtures"
        s = _store(root)
        for name in ("u", "gh", "my.api", "upstream-1", "a_b"):
            p = s._06(name, _fixture(f"f-{name}"))
            assert p.name == f"f-{name}.json"
            assert p.parent.name == name
            assert p.exists()
        assert len(list(s._07("gh"))) == 1


def test_06b_percent_encoding_is_not_traversal_at_this_layer():
    """The store sees the decoded name; the HTTP layer is what decodes it.

    ``%2e%2e`` is a legal filename, not a traversal, so the store must not
    reject it. What matters is that nodecoded ``..`` ever reaches the store,
    which tests/test_admin_api.py checks over real HTTP.
    """
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "fixtures"
        s = _store(root)
        p = s._05("%2e%2e", "f1")
        assert p.parent.name == "%2e%2e"
        assert p.parent.parent.resolve() == root.resolve()


def test_07_nested_directories_are_still_searched():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "fixtures"
        s = _store(root)
        s._06("u", _fixture("a"))
        (root / "u" / "deep").mkdir(parents=True)
        (root / "u" / "deep" / "b.json").write_text(
            json.dumps(_fixture("b")._07()))
        assert {f.id for f in s._07("u")} == {"a", "b"}


def test_08_unsafe_fixture_ids_are_rejected():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "fixtures"
        s = _store(root)
        for bad in ("..", "a/b", "a\\b", "", "con"):
            with pytest.raises(SecurityError):
                s._05("u", bad)


def test_09_content_addressed_ids_are_accepted(tmp_path):
    s = Store(tmp_path / "fixtures")
    fx = _fixture()
    fid = Store._09("u", fx.match)
    assert s._05("u", fid) == (tmp_path / "fixtures" / "u" / f"{fid}.json")


def test_10_absolute_upstream_is_rejected(tmp_path):
    s = Store(tmp_path / "fixtures")
    for bad in ("/etc", "C:\\Windows", "\\\\server\\share"):
        with pytest.raises(SecurityError):
            s._05(bad, "f1")
