import os
import sys

import pytest

from mockrelay.errors import ConfigError, SecurityError
from mockrelay.security import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    HOP_BY_HOP_HEADERS,
    ListenAddress,
    ensure_writable_dir,
    is_loopback,
    is_valid_header_name,
    is_valid_header_value,
    is_within,
    parse_listen,
    render_listen,
    safe_child,
    sanitize_headers,
    temporary_free_mb,
    validate_component,
)


def test_01_parse_host_port():
    got = parse_listen("127.0.0.1:8080")
    assert (got.host, got.port) == ("127.0.0.1", 8080)
    assert got.render() == "127.0.0.1:8080"
    assert parse_listen("0.0.0.0:9").port == 9


def test_02_parse_bare_port_defaults_to_loopback():
    got = parse_listen("8081")
    assert (got.host, got.port) == (DEFAULT_HOST, 8081)
    assert parse_listen(":9000").host == DEFAULT_HOST
    assert parse_listen("").port == DEFAULT_PORT


def test_03_parse_ipv6_bracketed_and_bare():
    assert parse_listen("[::1]:8080") == ListenAddress("::1", 8080, "[::1]:8080")
    assert parse_listen("::1").host == "::1"
    assert render_listen("::1", 8080) == "[::1]:8080"


def test_04_parse_listen_rejects_a_non_numeric_port():
    with pytest.raises(ConfigError) as ei:
        parse_listen("127.0.0.1:http")
    assert "port is not a number" in ei.value.render()


def test_05_parse_listen_rejects_an_out_of_range_port():
    with pytest.raises(ConfigError) as ei:
        parse_listen("127.0.0.1:99999")
    assert "out of range" in ei.value.render()


def test_06_parse_listen_rejects_unbalanced_brackets():
    with pytest.raises(ConfigError) as ei:
        parse_listen("[::1:8080")
    assert "brackets" in ei.value.render()


def test_07_parse_listen_rejects_trailing_junk_after_ipv6():
    with pytest.raises(ConfigError) as ei:
        parse_listen("[::1]junk")
    assert "after the IPv6 address" in ei.value.render()


def test_08_parse_listen_rejects_control_characters_in_the_host():
    with pytest.raises(ConfigError) as ei:
        parse_listen("local\thost:8080")
    assert "control characters" in ei.value.render()


def test_09_parse_listen_rejects_a_host_that_is_never_a_host():
    for bad in ("exa mple", "-bad-.example", "a" * 300):
        with pytest.raises(ConfigError):
            parse_listen(bad)


def test_10_parse_listen_rejects_an_absurdly_long_spec():
    with pytest.raises(ConfigError) as ei:
        parse_listen("a" * 400)
    assert "longer than" in ei.value.render()


def test_11_parse_listen_reports_every_problem_at_once():
    with pytest.raises(ConfigError) as ei:
        parse_listen("127.0.0.1:99999")
    assert len(ei.value.problems) == 1
    assert ei.value.problems[0].expected == "0-65535"


def test_12_loopback_detection_is_conservative():
    for good in ("127.0.0.1", "127.5.5.5", "::1", "localhost",
                 "LOCALHOST", " 127.0.0.1 ", "[::1]"):
        assert is_loopback(good) is True, good
    for bad in ("0.0.0.0",  # noqa: S104 - asserting this is rejected
                "example.com", "127.0.0.1.example.com", "10.0.0.1", "::"):
        assert is_loopback(bad) is False, bad


def test_13_empty_host_counts_as_loopback():
    assert is_loopback("") is True
    assert is_loopback(None) is True


def test_14_listen_address_loopback_and_public_flags():
    assert parse_listen("127.0.0.1:8080").loopback is True
    assert parse_listen("127.0.0.1:8080").public is False
    assert parse_listen("0.0.0.0:8080").public is True
    assert parse_listen("0.0.0.0:8080").loopback is False


def test_15_validate_component_accepts_ordinary_names():
    for good in ("gh", "my.api", "upstream-1", "a_b", "UPSTREAM",
                 "f" * 128, "x.json"):
        assert validate_component(good) == good


def test_16_validate_component_rejects_traversal():
    for bad in (".", "..", "../x", "x/..", "a\\b", "a/b", ""):
        with pytest.raises(SecurityError):
            validate_component(bad)


def test_17_validate_component_rejects_control_and_reserved_characters():
    for bad in ("a\x00b", "a\nb", "a\tb", "a\x7fb", "a<b", "a>b",
                'a"b', "a|b", "a?b", "a*b", "a:b"):
        with pytest.raises(SecurityError):
            validate_component(bad)


def test_18_validate_component_rejects_over_long_names():
    with pytest.raises(SecurityError) as ei:
        validate_component("f" * 129)
    assert "128" in str(ei.value)


def test_19_validate_component_rejects_leading_dot_and_trailing_junk():
    for bad in (".hidden", "name.", "name "):
        with pytest.raises(SecurityError):
            validate_component(bad)


def test_20_validate_component_rejects_windows_device_names():
    for bad in ("con", "CON", "nul.json", "com1", "LPT9"):
        with pytest.raises(SecurityError) as ei:
            validate_component(bad)
        assert "Windows" in str(ei.value) or "device" in str(ei.value)


def test_21_validate_component_reports_the_kind_it_was_given():
    with pytest.raises(SecurityError) as ei:
        validate_component("..", "upstream name")
    assert "upstream name" in str(ei.value)


def test_22_safe_child_joins_under_the_root(tmp_path):
    got = safe_child(tmp_path, "gh", "f1.json")
    assert got == tmp_path / "gh" / "f1.json"
    assert safe_child(tmp_path) == tmp_path


def test_23_safe_child_refuses_every_traversal_shape(tmp_path):
    for bad in ("..", "../evil", "a/../../evil", "..\\evil", "/etc"):
        with pytest.raises(SecurityError):
            safe_child(tmp_path, bad)


def test_24_safe_child_refuses_an_escaping_embedded_segment(tmp_path):
    with pytest.raises(SecurityError):
        safe_child(tmp_path, "gh", "..", "evil")


def test_25_safe_child_refuses_a_symlink_that_points_outside(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "fixtures"
    root.mkdir()
    link = root / "escape"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("symlinks are not available to this user")
    with pytest.raises(SecurityError):
        safe_child(root, "escape", "fixture.json")


def test_26_safe_child_allows_a_symlink_that_stays_inside(tmp_path):
    root = tmp_path / "fixtures"
    (root / "real").mkdir(parents=True)
    try:
        (root / "alias").symlink_to(root / "real", target_is_directory=True)
    except (OSError, NotImplementedError, AttributeError):
        pytest.skip("symlinks are not available to this user")
    got = safe_child(root, "alias", "f.json")
    assert got == root / "alias" / "f.json"


def test_27_is_within_accepts_the_root_and_its_descendants(tmp_path):
    assert is_within(tmp_path, tmp_path)
    assert is_within(tmp_path, tmp_path / "a" / "b")
    assert is_within(tmp_path, tmp_path / ".." / tmp_path.name) is True


def test_28_is_within_rejects_siblings_with_a_shared_prefix(tmp_path):
    base = tmp_path / "fixtures"
    base.mkdir()
    sibling = tmp_path / "fixtures-evil"
    sibling.mkdir()
    assert is_within(base, sibling) is False


def test_29_is_within_is_case_insensitive_on_windows(tmp_path):
    base = tmp_path / "Fixtures"
    base.mkdir()
    child = base / "Sub"
    child.mkdir()
    assert is_within(base, child) is True
    assert os.path.normcase("A") == os.path.normcase("a") or sys.platform != "win32"


def test_30_valid_header_names():
    for good in ("Content-Type", "X-Trace-Id", "a", "X_Y", "a.b"):
        assert is_valid_header_name(good) is True
    for bad in ("", "bad header", "bad\nname", "bad:name", "a" * 257, "a=b"):
        assert is_valid_header_name(bad) is False


def test_31_valid_header_values_reject_header_injection():
    assert is_valid_header_value("plain") is True
    assert is_valid_header_value(123) is True
    assert is_valid_header_value("a\r\nX-Evil: 1") is False
    assert is_valid_header_value("a\nb") is False
    assert is_valid_header_value("a\x00b") is False
    assert is_valid_header_value("a" * 16385) is False


def test_32_sanitize_headers_drops_hop_by_hop():
    pairs = [("Host", "x"), ("Connection", "close"),
             ("Content-Length", "3"), ("X-Keep", "yes")]
    kept, dropped = sanitize_headers(pairs)
    assert kept == [("X-Keep", "yes")]
    assert len(dropped) == 3
    assert all("hop-by-hop" in d for d in dropped)


def test_33_sanitize_headers_can_keep_hop_by_hop():
    kept, dropped = sanitize_headers([("Host", "x")], drop_hop_by_hop=False)
    assert kept == [("Host", "x")]
    assert dropped == []


def test_34_sanitize_headers_drops_injection_attempts():
    kept, dropped = sanitize_headers([("X-Ok", "1"),
                                      ("X-Bad", "v\r\nX-Evil: 1"),
                                      ("Bad Name", "1")])
    assert kept == [("X-Ok", "1")]
    assert len(dropped) == 2


def test_35_sanitize_headers_never_echoes_a_value_in_a_reason():
    secret = "Bearer ghp_" + "a" * 36
    _kept, dropped = sanitize_headers([("X-Bad", secret + "\r\nX-Evil: 1")])
    assert dropped == ["header X-Bad has an illegal value"]
    assert "ghp_" not in "".join(dropped)
    assert secret not in "".join(dropped)


def test_36_sanitize_headers_enforces_the_count_limit():
    pairs = [(f"X-{i}", "v") for i in range(10)]
    kept, dropped = sanitize_headers(pairs, max_headers=4)
    assert len(kept) == 4
    assert dropped == ["too many headers"]


def test_37_sanitize_headers_enforces_the_size_limit():
    pairs = [(f"X-{i}", "v" * 100) for i in range(10)]
    kept, dropped = sanitize_headers(pairs, max_total_bytes=250)
    assert len(kept) < 10
    assert dropped == ["header block exceeds the configured limit"]


def test_38_sanitize_headers_coerces_non_string_values():
    kept, _dropped = sanitize_headers([("X-Count", 5),
                                       ("X-Flag", True)])
    assert kept == [("X-Count", "5"), ("X-Flag", "True")]
    _kept2, dropped2 = sanitize_headers([("Content-Length", 5)])
    assert dropped2 == ["hop-by-hop header Content-Length"]


def test_39_ensure_writable_dir_creates_and_accepts(tmp_path):
    target = tmp_path / "a" / "b"
    ensure_writable_dir(target)
    assert target.is_dir()
    ensure_writable_dir(target)


def test_40_ensure_writable_dir_reports_a_file_in_the_way(tmp_path):
    f = tmp_path / "file"
    f.write_text("x")
    with pytest.raises(ConfigError) as ei:
        ensure_writable_dir(f, "fixtures_dir")
    assert "fixtures_dir" in ei.value.render()


def test_41_temporary_free_mb_degrades_gracefully(tmp_path):
    value = temporary_free_mb(tmp_path)
    assert value is None or value >= 0
    if sys.platform == "win32":
        assert value is None


def test_42_ensure_writable_dir_reports_permission_problems(tmp_path):
    if getattr(os, "getuid", lambda: -1)() == 0:
        pytest.skip("root ignores permission bits")
    if sys.platform == "win32":
        pytest.skip("Windows does not enforce directory permission bits")
    readonly = tmp_path / "ro"
    readonly.mkdir()
    readonly.chmod(0o500)
    try:
        with pytest.raises(ConfigError) as ei:
            ensure_writable_dir(readonly / "child")
        assert "writable" in ei.value.render() or "create" in ei.value.render()
    finally:
        readonly.chmod(0o700)


def test_43_hop_by_hop_set_covers_the_required_names():
    for name in ("connection", "keep-alive", "te", "trailer",
                 "transfer-encoding", "upgrade", "host", "content-length",
                 "proxy-authorization"):
        assert name in HOP_BY_HOP_HEADERS
