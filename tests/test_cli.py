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


def test_05b_a_port_of_zero_picks_a_free_port():
    """`host:0` is how a caller asks the OS for an unused port.

    Rejecting it silently moved every such caller onto the default port,
    which then collided when several servers were up at once.
    """
    cfg = _load({"listen": "127.0.0.1:0", "admin_listen": "127.0.0.1:0"})
    assert cfg.problems == []
    assert cfg.listen == "127.0.0.1:0"
    assert cfg.admin_listen == "127.0.0.1:0"


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


def _fixture(upstream="gh", path="/users/octocat", status=200):
    return {
        "id": f"{upstream}-get-{abs(hash(path)) % 10000:04d}",
        "upstream": upstream,
        "match": {"method": "GET", "path": path},
        "request": {
            "method": "GET",
            "path": path,
            "query": {},
            "headers": {},
            "body": None,
        },
        "response": {"status": status, "headers": {}, "body": {"ok": True}},
        "normalize": [],
        "recorded_at": "2024-01-01T00:00:00Z",
        "call_index": 0,
    }


def _config_file(tmp_path, extra=""):
    d = str(tmp_path / "fixtures").replace("\\", "/")
    path = tmp_path / "mockrelay.yaml"
    path.write_text(f"fixtures_dir: '{d}'\nmode: replay\n{extra}", encoding="utf-8")
    return path


def test_16_a_sound_config_and_tree_exit_zero(tmp_path, capsys):
    import json

    path = _config_file(tmp_path)
    tree = tmp_path / "fixtures" / "gh"
    tree.mkdir(parents=True)
    (tree / "a.json").write_text(json.dumps(_fixture()), encoding="utf-8")
    code, out, _ = _run(["validate", "-c", str(path)], capsys)
    assert code == 0
    assert "no problems" in out
    assert "Traceback" not in out


def test_17_an_empty_tree_is_valid(tmp_path, capsys):
    path = _config_file(tmp_path)
    code, _, _ = _run(["validate", "-c", str(path)], capsys)
    assert code == 0


def test_18_a_bad_setting_exits_validation_failed(tmp_path, capsys):
    from mockrelay.errors import EXIT_VALIDATION

    path = _config_file(tmp_path, "latency_ms: soon\n")
    code, out, _ = _run(["validate", "-c", str(path)], capsys)
    assert code == EXIT_VALIDATION
    assert "latency_ms" in out


def test_19_a_broken_fixture_exits_validation_failed(tmp_path, capsys):
    import json

    from mockrelay.errors import EXIT_VALIDATION

    path = _config_file(tmp_path)
    tree = tmp_path / "fixtures" / "gh"
    tree.mkdir(parents=True)
    (tree / "broken.json").write_text(json.dumps({"id": "x"}), encoding="utf-8")
    code, out, _ = _run(["validate", "-c", str(path)], capsys)
    assert code == EXIT_VALIDATION
    assert "broken.json" in out


def test_20_an_unparseable_config_exits_config_error(tmp_path, capsys):
    from mockrelay.errors import EXIT_CONFIG

    path = tmp_path / "mockrelay.yaml"
    path.write_text("listen: [unclosed\n", encoding="utf-8")
    code, out, _ = _run(["validate", "-c", str(path)], capsys)
    assert code == EXIT_CONFIG
    assert "Configuration error" in out
    assert "Traceback" not in out


def test_21_validate_reports_every_problem_not_just_the_first(tmp_path, capsys):
    path = _config_file(tmp_path, "latency_ms: soon\nmode: sideways\n")
    _, out, _ = _run(["validate", "-c", str(path)], capsys)
    assert "latency_ms" in out
    assert "mode" in out


def test_22_validate_defaults_to_mockrelay_yaml(tmp_path, capsys, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mockrelay.yaml").write_text(
        "fixtures_dir: './fx'\nmode: replay\n", encoding="utf-8"
    )
    code, out, _ = _run(["validate"], capsys)
    assert code == 0
    assert "Traceback" not in out


def _tree_with(tmp_path, count=1, upstream="gh"):

    from mockrelay._10 import _04 as Store

    store = Store(tmp_path / "fixtures")
    for i in range(count):
        store._06(upstream, _fixture_obj(upstream, f"/things/{i}"))
    return tmp_path / "fixtures"


def _fixture_obj(upstream, path, status=200, recorded_at=None):
    from mockrelay._06 import _01 as Match
    from mockrelay._06 import _04 as Request
    from mockrelay._06 import _05 as Response
    from mockrelay._06 import _06 as Fixture

    return Fixture(
        id=f"{upstream}-get-{abs(hash(path)) % 100000:05d}",
        upstream=upstream,
        match=Match(method="GET", path=path),
        request=Request(method="GET", path=path),
        response=Response(status=status, headers={}, body={"ok": True}),
        recorded_at=recorded_at,
    )


def test_23_stats_reports_a_count_per_upstream(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=3)
    code, out, _ = _run(["stats", "-c", str(path)], capsys)
    assert code == 0
    assert "gh" in out
    assert "3" in out


def test_24_stats_reports_an_empty_store(tmp_path, capsys):
    path = _config_file(tmp_path)
    code, out, _ = _run(["stats", "-c", str(path)], capsys)
    assert code == 0
    assert "no fixtures" in out.lower()


def test_25_stats_can_be_limited_to_one_upstream(tmp_path, capsys):
    import json

    from mockrelay._10 import _04 as Store

    path = _config_file(tmp_path)
    store = Store(tmp_path / "fixtures")
    store._06("gh", _fixture_obj("gh", "/a"))
    store._06("stripe", _fixture_obj("stripe", "/b"))
    code, out, _ = _run(["stats", "-c", str(path), "-u", "gh"], capsys)
    assert code == 0
    assert "gh" in out
    assert json.dumps("stripe") not in out


def test_26_clean_without_yes_only_reports(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    path = _config_file(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    from mockrelay._10 import _04 as Store

    store = Store(tmp_path / "fixtures")
    stored = store._06("gh", _fixture_obj("gh", "/old", recorded_at=old))
    code, out, _ = _run(["clean", "-c", str(path), "--older-than", "30"], capsys)
    assert code == 0
    assert stored.exists()
    assert "would remove" in out.lower()


def test_27_clean_with_yes_removes_old_fixtures(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    path = _config_file(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    from mockrelay._10 import _04 as Store

    store = Store(tmp_path / "fixtures")
    old_path = store._06("gh", _fixture_obj("gh", "/old", recorded_at=old))
    new_path = store._06("gh", _fixture_obj("gh", "/new"))
    code, out, _ = _run(
        ["clean", "-c", str(path), "--older-than", "30", "--yes"], capsys
    )
    assert code == 0
    assert not old_path.exists()
    assert new_path.exists()
    assert "removed" in out.lower()


def test_28_clean_nothing_to_do_says_so(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=1)
    code, out, _ = _run(
        ["clean", "-c", str(path), "--older-than", "30", "--yes"], capsys
    )
    assert code == 0
    assert "nothing" in out.lower()


def test_29_clean_can_be_limited_to_one_upstream(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    path = _config_file(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    from mockrelay._10 import _04 as Store

    store = Store(tmp_path / "fixtures")
    gh = store._06("gh", _fixture_obj("gh", "/old", recorded_at=old))
    stripe = store._06("stripe", _fixture_obj("stripe", "/old", recorded_at=old))
    _run(["clean", "-c", str(path), "--older-than", "30", "--yes", "-u", "gh"], capsys)
    assert not gh.exists()
    assert stripe.exists()


def test_30_clean_needs_a_positive_age(tmp_path, capsys):
    from mockrelay.errors import EXIT_USAGE

    path = _config_file(tmp_path)
    code, _, _ = _run(["clean", "-c", str(path), "--older-than", "0", "--yes"], capsys)
    assert code == EXIT_USAGE


def _json_run(argv, capsys):
    import json

    code, out, err = _run(argv, capsys)
    assert "Traceback" not in out
    return code, json.loads(out), err


def test_31_list_json_is_an_envelope(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=2)
    code, doc, _ = _json_run(["list", "-c", str(path), "--json"], capsys)
    assert code == 0
    assert doc["schema"] == 1
    assert doc["command"] == "list"
    assert doc["ok"] is True
    assert doc["data"]["count"] == 2
    assert doc["data"]["fixtures"][0]["upstream"] == "gh"


def test_32_list_json_on_an_empty_store_is_still_ok(tmp_path, capsys):
    path = _config_file(tmp_path)
    code, doc, _ = _json_run(["list", "-c", str(path), "--json"], capsys)
    assert code == 0
    assert doc["ok"] is True
    assert doc["data"]["fixtures"] == []


def test_33_stats_json_carries_totals(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=3)
    code, doc, _ = _json_run(["stats", "-c", str(path), "--json"], capsys)
    assert code == 0
    assert doc["data"]["total_fixtures"] == 3
    assert doc["data"]["total_bytes"] > 0
    assert doc["data"]["upstreams"][0]["upstream"] == "gh"


def test_34_validate_json_reports_problems_and_exit_code(tmp_path, capsys):
    from mockrelay.errors import EXIT_VALIDATION

    d = tmp_path / "fixtures"
    d.mkdir()
    (d / "bad.json").write_text('{"id": "x"}', encoding="utf-8")
    path = tmp_path / "mockrelay.yaml"
    path.write_text(f"fixtures_dir: '{d}'\nmode: replay\n", encoding="utf-8")
    code, doc, _ = _json_run(["validate", "-c", str(path), "--json"], capsys)
    assert code == EXIT_VALIDATION
    assert doc["ok"] is False
    assert doc["problems"]
    assert doc["data"]["problems_found"] >= 1


def test_35_validate_json_on_a_sound_tree_is_ok(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=1)
    code, doc, _ = _json_run(["validate", "-c", str(path), "--json"], capsys)
    assert code == 0
    assert doc["ok"] is True
    assert "problems" not in doc


def test_36_validate_json_reports_a_missing_config(tmp_path, capsys):
    from mockrelay.errors import EXIT_CONFIG

    code, doc, _ = _json_run(
        ["validate", "-c", str(tmp_path / "nope.yaml"), "--json"], capsys
    )
    assert code == EXIT_CONFIG
    assert doc["ok"] is False
    assert doc["problems"]


def test_37_match_json_carries_the_candidates(tmp_path, capsys):
    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=1)
    code, doc, _ = _json_run(["match", "/things/0", "-c", str(path), "--json"], capsys)
    assert code == 0
    assert doc["command"] == "match"
    assert doc["data"]["candidates"]
    assert doc["data"]["candidates"][0]["matched"] is True


def test_38_clean_json_previews_without_deleting(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    from mockrelay._10 import _04 as Store

    path = _config_file(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    store = Store(tmp_path / "fixtures")
    stored = store._06("gh", _fixture_obj("gh", "/old", recorded_at=old))
    code, doc, _ = _json_run(
        ["clean", "-c", str(path), "--older-than", "30", "--json"], capsys
    )
    assert code == 0
    assert doc["data"]["dry_run"] is True
    assert doc["data"]["removed"] == []
    assert len(doc["data"]["candidates"]) == 1
    assert stored.exists()


def test_39_clean_json_deletes_when_asked(tmp_path, capsys):
    from datetime import datetime, timedelta, timezone

    from mockrelay._10 import _04 as Store

    path = _config_file(tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=90)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    store = Store(tmp_path / "fixtures")
    stored = store._06("gh", _fixture_obj("gh", "/old", recorded_at=old))
    code, doc, _ = _json_run(
        ["clean", "-c", str(path), "--older-than", "30", "--yes", "--json"], capsys
    )
    assert code == 0
    assert doc["data"]["dry_run"] is False
    assert len(doc["data"]["removed"]) == 1
    assert not stored.exists()


def test_40_json_output_is_pure_json(tmp_path, capsys):
    """A script parsing stdout must not have to strip a banner first."""
    import json

    path = _config_file(tmp_path)
    _tree_with(tmp_path, count=1)
    code, out, _ = _run(["stats", "-c", str(path), "--json"], capsys)
    assert code == 0
    json.loads(out)


_BAD = "listen: '127.0.0.1:99999'\nmode: replay\n"


@pytest.mark.parametrize(
    "argv",
    [
        ["list"],
        ["match", "/x"],
        ["stats"],
        ["clean", "--yes"],
    ],
)
def test_41_a_bad_config_exits_with_the_config_code(
    tmp_path, capsys, monkeypatch, argv
):
    from mockrelay.errors import EXIT_CONFIG

    monkeypatch.chdir(tmp_path)
    (tmp_path / "mockrelay.yaml").write_text(_BAD, encoding="utf-8")
    code, out, err = _run(argv, capsys)
    assert code == EXIT_CONFIG
    assert "Traceback" not in out + err
    assert "listen" in (out + err)


def test_42_a_bad_config_message_goes_to_stderr(tmp_path, capsys, monkeypatch):
    """Stdout is for data; a script parsing it must not see an error."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "mockrelay.yaml").write_text(_BAD, encoding="utf-8")
    _code, out, err = _run(["list"], capsys)
    assert out.strip() == ""
    assert err.strip() != ""


def test_43_a_bad_config_with_json_emits_a_json_error(tmp_path, capsys, monkeypatch):
    from mockrelay.errors import EXIT_CONFIG

    monkeypatch.chdir(tmp_path)
    (tmp_path / "mockrelay.yaml").write_text(_BAD, encoding="utf-8")
    code, doc, _ = _json_run(["list", "--json"], capsys)
    assert code == EXIT_CONFIG
    assert doc["ok"] is False
    assert doc["problems"]


def test_44_bind_failure_uses_the_generic_error_code(tmp_path, capsys, monkeypatch):
    """A port already in use is a runtime error, not a usage error."""
    import socket

    from mockrelay.errors import EXIT_ERROR

    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    other = socket.socket()
    other.bind(("127.0.0.1", 0))
    admin_port = other.getsockname()[1]
    other.close()
    path = tmp_path / "mockrelay.yaml"
    path.write_text(
        f"listen: '127.0.0.1:{port}'\nadmin_listen: '127.0.0.1:{admin_port}'\n"
        "mode: replay\n",
        encoding="utf-8",
    )
    try:
        code, _, err = _run(["serve", "-c", str(path)], capsys)
    finally:
        sock.close()
    assert code == EXIT_ERROR
    assert "Traceback" not in err
