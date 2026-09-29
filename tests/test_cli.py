"""The CLI answers questions a user asks before starting a server.

A recorded fixture set is only useful if the tool can tell you what is in
it, whether it is still valid, and what it would match, without binding a
port or reaching the network. These tests drive the real entry point and
assert on what lands on stdout and in the exit code, because that is the
whole contract: the exit code is what a CI step reads and stdout is what a
human reads.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from mockrelay._15 import _40
from mockrelay._version import __version__


def _run(argv, capsys):
    """Run the CLI, returning (exit_code, stdout, stderr)."""
    code = 0
    try:
        _40(argv)
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else 1
    out = capsys.readouterr()
    return code, out.out, out.err


# --version


def test_01_version_prints_the_package_version(capsys):
    code, out, _ = _run(["--version"], capsys)
    assert code == 0
    assert __version__ in out


def test_02_version_matches_the_installed_package(capsys):
    """The flag and the metadata cannot drift, because both read one file."""
    import importlib.metadata

    code, _out, _ = _run(["--version"], capsys)
    assert code == 0
    try:
        assert importlib.metadata.version("mockrelay") == __version__
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("mockrelay is not installed in this environment")


def test_03_version_does_not_need_a_config_or_a_store(tmp_path, monkeypatch):
    """--version must not create a fixtures directory as a side effect."""
    monkeypatch.chdir(tmp_path)
    proc = subprocess.run(
        [sys.executable, "-m", "mockrelay", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert __version__ in proc.stdout
    assert not (tmp_path / "fixtures").exists()


# config validation


def _load(data):
    """Build a Config from a dict, the way a parsed YAML document arrives."""
    from mockrelay._05 import _06

    return _06(data)


def _problems(data):
    cfg = _load(data)
    return [p.render() for p in cfg.problems]


def _subjects(data):
    cfg = _load(data)
    return [p.subject for p in cfg.problems]


def test_04_a_sound_config_reports_no_problems(tmp_path):
    cfg = _load(
        {
            "listen": "127.0.0.1:8080",
            "admin_listen": "127.0.0.1:8081",
            "fixtures_dir": str(tmp_path / "fixtures"),
            "mode": "replay",
            "latency_ms": 0,
            "match_mode": "auto",
            "fuzzy_threshold": 0.86,
            "match_priority": ["path", "body", "query", "literal"],
            "redact_headers": ["authorization", "cookie"],
            "normalize_json_paths": ["$.id"],
            "upstreams": {"gh": {"base_url": "https://api.github.com"}},
        }
    )
    assert cfg.problems == []
    assert cfg.mode == "replay"
    assert cfg.upstreams["gh"].base_url == "https://api.github.com"


@pytest.mark.parametrize(
    ("data", "subject"),
    [
        ({"latency_ms": "soon"}, "latency_ms:"),
        ({"latency_ms": -1}, "latency_ms:"),
        ({"fuzzy_threshold": "high"}, "fuzzy_threshold:"),
        ({"fuzzy_threshold": 1.5}, "fuzzy_threshold:"),
        ({"fuzzy_threshold": -0.1}, "fuzzy_threshold:"),
        ({"mode": "sideways"}, "mode:"),
        ({"match_mode": "sortof"}, "match_mode:"),
        ({"listen": "nope"}, "listen:"),
        ({"listen": "127.0.0.1"}, "listen:"),
        ({"listen": "127.0.0.1:99999"}, "listen:"),
        ({"listen": 8080}, "listen:"),
        ({"admin_listen": "host:notaport"}, "admin_listen:"),
        ({"redact_headers": "authorization"}, "redact_headers:"),
        ({"redact_headers": [1, 2]}, "redact_headers:"),
        ({"normalize_json_paths": "$.id"}, "normalize_json_paths:"),
        ({"match_priority": ["path", "colour"]}, "match_priority:"),
        ({"match_priority": "path"}, "match_priority:"),
        ({"ignore_case": "maybe"}, "ignore_case:"),
        ({"fixtures_dir": []}, "fixtures_dir:"),
        ({"upstreams": ["a"]}, "upstreams:"),
        ({"upstreams": {"gh": {}}}, "gh:"),
        ({"upstreams": {"gh": {"base_url": 12}}}, "gh.base_url:"),
        (
            {"upstreams": {"gh": {"base_url": "http://x", "mode": "sideways"}}},
            "gh.mode:",
        ),
        ({"upstreams": {"gh": {"base_url": "http://x", "routes": []}}}, "gh.routes:"),
        ({"error_injection": "always"}, "error_injection:"),
        ({"error_injection": {"status": "oops"}}, "error_injection.status:"),
        ({"error_injection": {"rate": 5}}, "error_injection.rate:"),
    ],
)
def test_05_bad_settings_are_reported_not_raised(data, subject):
    assert subject in _subjects(data)


def test_06_wrongly_typed_booleans_are_reported():
    for key in (
        "ignore_case",
        "fuzzy_enabled",
        "metrics_enabled",
        "sequential",
        "smart_record_paths",
    ):
        assert f"{key}:" in _subjects({key: "maybe"})


def test_07_a_typo_in_a_key_is_reported():
    """The failure mode this exists for: a silent no-op setting."""
    problems = _problems({"base_ur1": "https://example.com"})
    assert any("base_ur1" in p for p in problems)


def test_08_an_unknown_upstream_key_is_reported():
    problems = _problems(
        {"upstreams": {"gh": {"base_url": "http://x", "md": "replay"}}}
    )
    assert any("md" in p for p in problems)


def test_09_a_fixtures_dir_that_is_a_file_is_reported(tmp_path):
    blocked = tmp_path / "not-a-dir"
    blocked.write_text("hello", encoding="utf-8")
    problems = _problems({"fixtures_dir": str(blocked)})
    assert any("fixtures_dir" in p for p in _subjects({"fixtures_dir": str(blocked)}))
    assert problems


def test_10_every_problem_carries_an_expectation():
    """A message that does not say what was wanted is not actionable."""
    from mockrelay._05 import _06

    cfg = _06({"mode": "sideways", "latency_ms": "soon"})
    assert cfg.problems
    assert all(p.expected for p in cfg.problems)


def test_11_a_bad_config_still_yields_usable_defaults():
    """Loading must not explode, so `validate` can describe what is wrong."""
    cfg = _load({"latency_ms": "soon", "mode": "sideways"})
    assert cfg.latency_ms == 0
    assert cfg.mode in ("record", "replay", "passthrough", "hybrid")
    assert cfg.problems


# config loading


def test_12_unparseable_yaml_raises_a_config_error(tmp_path):
    from mockrelay._05 import _06
    from mockrelay.errors import ConfigLoadError

    path = tmp_path / "mockrelay.yaml"
    path.write_text("listen: [unclosed\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError) as e:
        _06._07(path)
    assert "mockrelay.yaml" in e.value.source
    assert "at line" in e.value.render()


def test_13_a_config_that_is_a_directory_is_a_config_error(tmp_path):
    from mockrelay._05 import _06
    from mockrelay.errors import ConfigLoadError

    with pytest.raises(ConfigLoadError):
        _06._07(tmp_path)


def test_14_a_yaml_document_that_is_not_a_mapping_is_a_config_error(tmp_path):
    from mockrelay._05 import _06
    from mockrelay.errors import ConfigLoadError

    path = tmp_path / "mockrelay.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(ConfigLoadError):
        _06._07(path)


def test_15_a_missing_config_file_still_loads_defaults(tmp_path):
    from mockrelay._05 import _06

    cfg = _06._07(tmp_path / "absent.yaml")
    assert cfg.problems == []
    assert cfg.mode == "record"
