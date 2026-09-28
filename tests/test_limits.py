import pytest

from mockrelay.errors import Problem
from mockrelay.limits import DEFAULT_LIMITS, KiB, Limits, MiB


def test_01_defaults_are_sane_and_ordered():
    d = DEFAULT_LIMITS.as_dict()
    assert d["max_request_body"] == 10 * MiB
    assert d["max_response_body"] == 50 * MiB
    assert d["max_fixture_bytes"] == 16 * MiB
    assert d["max_config_bytes"] == 4 * MiB
    assert d["max_header_bytes"] == 64 * KiB
    assert d["max_request_target"] == 8 * KiB
    assert d["upstream_timeout"] == 30.0
    assert d["connect_timeout"] == 10.0
    assert d["max_redirects"] == 5


def test_02_limits_are_frozen():
    with pytest.raises(Exception):
        DEFAULT_LIMITS.max_request_body = 1


def test_03_field_names_matches_the_dataclass():
    assert Limits.field_names() == tuple(DEFAULT_LIMITS.as_dict())
    assert "max_request_body" in Limits.field_names()


def test_04_replace_overrides_only_named_fields():
    new = DEFAULT_LIMITS.replace(max_request_body=1, not_a_field=2)
    assert new.max_request_body == 1
    assert new.max_response_body == DEFAULT_LIMITS.max_response_body


def test_05_replace_leaves_the_original_untouched():
    base = DEFAULT_LIMITS.replace(max_request_body=7)
    assert base.max_request_body == 7
    assert DEFAULT_LIMITS.max_request_body == 10 * MiB
    assert base is not DEFAULT_LIMITS


def test_06_coerce_accepts_a_valid_mapping():
    got, problems = Limits.coerce({"max_request_body": 1024,
                                  "upstream_timeout": 5})
    assert problems == []
    assert got.max_request_body == 1024
    assert got.upstream_timeout == 5.0
    assert got.max_response_body == DEFAULT_LIMITS.max_response_body


def test_07_coerce_rejects_a_non_mapping():
    got, problems = Limits.coerce(["max_request_body"])
    assert got == DEFAULT_LIMITS
    assert len(problems) == 1
    assert "mapping" in problems[0].problem
    assert "max_request_body" in problems[0].expected


def test_08_coerce_rejects_unknown_names():
    got, problems = Limits.coerce({"max_flavour_bytes": 1})
    assert problems[0].subject == "`max_flavour_bytes`"
    assert "not a known limit" in problems[0].problem
    assert got == DEFAULT_LIMITS


def test_09_coerce_rejects_non_numbers():
    for bad in ("10", True, None, [1], {"a": 1}):
        _got, problems = Limits.coerce({"max_request_body": bad})
        assert [p.problem for p in problems] == ["must be a number"]


def test_10_coerce_rejects_non_positive_values():
    for bad in (0, -1, -0.5):
        _got, problems = Limits.coerce({"max_request_body": bad})
        assert [p.problem for p in problems] == ["must be greater than zero"]


def test_11_coerce_clamps_timeouts_to_a_sane_range():
    _got, problems = Limits.coerce({"upstream_timeout": 0})
    assert "greater than zero" in problems[0].problem
    _got, problems = Limits.coerce({"connect_timeout": 99999})
    assert "between 0 and 3600" in problems[0].problem
    got, problems = Limits.coerce({"connect_timeout": 3600})
    assert problems == []
    assert got.connect_timeout == 3600.0


def test_12_coerce_keeps_integer_limits_integral():
    got, _p = Limits.coerce({"max_request_body": 1024.0})
    assert isinstance(got.max_request_body, int)


def test_13_coerce_reports_every_bad_entry_at_once():
    _got, problems = Limits.coerce({"nope": 1, "max_request_body": -1,
                                    "max_headers": "x"})
    assert len(problems) == 3
    assert all(isinstance(p, Problem) for p in problems)


def test_14_coerce_keeps_good_entries_alongside_bad_ones():
    got, problems = Limits.coerce({"max_headers": 4, "nope": 1})
    assert len(problems) == 1
    assert got.max_headers == 4


def test_15_coerce_of_empty_mapping_is_the_default():
    got, problems = Limits.coerce({})
    assert problems == []
    assert got == DEFAULT_LIMITS
