import pytest

from mockrelay.errors import (
    EXIT_CONFIG,
    EXIT_DOCTOR,
    EXIT_ERROR,
    EXIT_INTERRUPTED,
    EXIT_OK,
    EXIT_USAGE,
    EXIT_VALIDATION,
    ConfigError,
    ConfigLoadError,
    DoctorFailed,
    FixtureError,
    FixtureSchemaError,
    LimitExceeded,
    MockRelayError,
    Problem,
    SecurityError,
    StoreError,
    UpstreamError,
    ValidationFailed,
    as_problems,
    render_problems,
)


def test_01_exit_codes_are_distinct_and_conventional():
    codes = [EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_CONFIG, EXIT_VALIDATION,
             EXIT_DOCTOR, EXIT_INTERRUPTED]
    assert codes[:6] == [0, 1, 2, 3, 4, 5]
    assert EXIT_INTERRUPTED == 130
    assert len(set(codes)) == len(codes)


def test_02_problem_renders_subject_expected_and_location():
    p = Problem("is not a number", subject="`port`", expected="0-65535",
                location="127.0.0.1:99999")
    out = p.render()
    assert out.splitlines() == [
        "`port` is not a number",
        "Expected: 0-65535",
        "  at: 127.0.0.1:99999",
    ]


def test_03_problem_does_not_duplicate_an_explicit_subject():
    p = Problem("`port` is not a number", subject="`port`")
    assert p.render().count("`port`") == 1


def test_04_problem_omits_absent_fields_from_dict():
    assert Problem("boom").as_dict() == {"problem": "boom"}
    assert Problem("boom", subject="s").as_dict() == {"problem": "boom",
                                                      "subject": "s"}


def test_05_render_problems_headers_and_hint():
    out = render_problems("Configuration error", [Problem("bad")],
                          source="mockrelay.yaml", hint="Fix it.")
    assert out.splitlines() == [
        "Configuration error", "", "File:", "  mockrelay.yaml", "",
        "Problem:", "bad", "", "Next:", "  Fix it.",
    ]


def test_06_render_problems_truncates_and_counts_the_rest():
    problems = [Problem(f"problem {i}") for i in range(5)]
    out = render_problems("Configuration error", problems, limit=2)
    assert "problem 1" in out
    assert "problem 2" not in out
    assert "... and 3 more problem(s)" in out


def test_07_render_problems_indents_after_the_first():
    out = render_problems("k", [Problem("a", expected="b"), Problem("c")])
    body = out.split("Problem:", 1)[1]
    assert "a\nExpected: b" in body
    assert "  c" in body


def test_08_base_error_carries_message_source_and_hint():
    err = MockRelayError("nope", source="f.yaml", hint="try again")
    assert err.message == "nope"
    assert err.source == "f.yaml"
    assert err.hint == "try again"
    assert err.exit_code == EXIT_ERROR
    assert "nope" in err.render()


def test_09_base_error_exit_code_can_be_overridden():
    err = MockRelayError("nope", exit_code=EXIT_USAGE)
    assert err.exit_code == EXIT_USAGE


def test_10_config_error_exit_code_and_default_hint():
    err = ConfigError([Problem("first"), Problem("second")])
    assert err.exit_code == EXIT_CONFIG
    assert err.message == "first"
    out = err.render()
    assert "Configuration error" in out
    assert "first" in out and "second" in out
    assert "mockrelay validate" in out


def test_11_config_error_with_no_problems_still_renders():
    err = ConfigError([])
    assert err.message == "the problem was not described"
    assert "the problem was not described" in err.render()


def test_11b_bare_strings_are_accepted_where_problems_are():
    err = ConfigError("something went wrong")
    assert err.message == "something went wrong"
    assert "something went wrong" in err.render()
    assert FixtureSchemaError("missing status").message == "missing status"
    assert ValidationFailed("bad fixture").message == "bad fixture"
    assert DoctorFailed("old python").message == "old python"


def test_11c_a_single_problem_object_is_accepted():
    p = Problem("boom")
    assert ConfigError(p).problems == [p]
    assert as_problems([])[0].problem == "the problem was not described"
    assert len(as_problems(["a", "b"])) == 2
    assert as_problems(42)[0].problem == "42"


def test_12_config_load_error_is_a_config_error():
    assert issubclass(ConfigLoadError, ConfigError)
    assert ConfigLoadError([Problem("x")]).exit_code == EXIT_CONFIG


def test_13_fixture_error_hierarchy():
    assert issubclass(FixtureError, MockRelayError)
    assert issubclass(StoreError, FixtureError)
    err = FixtureSchemaError([Problem("missing status")], source="a.json")
    assert "Invalid fixture" in err.render()
    assert "a.json" in err.render()
    assert "missing status" in err.render()


def test_14_security_and_upstream_errors():
    assert issubclass(SecurityError, MockRelayError)
    assert issubclass(UpstreamError, MockRelayError)
    assert "Refused for security reasons" in SecurityError("bad path").render()


def test_15_limit_exceeded_defaults_to_413_and_is_overridable():
    err = LimitExceeded("body too large")
    assert err.status == 413
    assert LimitExceeded("headers", status=431).status == 431
    assert err.exit_code == EXIT_ERROR


def test_16_validation_failed_exit_code():
    err = ValidationFailed([Problem("fixture 3 is unreadable")])
    assert err.exit_code == EXIT_VALIDATION
    assert "Validation failed" in err.render()
    assert "fixture 3 is unreadable" in err.render()


def test_17_doctor_failed_exit_code():
    err = DoctorFailed([Problem("python is too old")])
    assert err.exit_code == EXIT_DOCTOR
    assert "Environment check failed" in err.render()


def test_18_error_rendering_scrubs_secrets():
    err = MockRelayError("failed with token ghp_" + "a" * 36)
    out = err.render()
    assert "ghp_" + "a" * 36 not in out
    assert "{{SECRET}}" in out


def test_19_problem_rendering_scrubs_secrets():
    out = render_problems("k", [Problem("saw AKIA" + "A" * 16)])
    assert "AKIA" + "A" * 16 not in out
    assert "{{SECRET}}" in out


def test_20_every_error_is_catchable_as_exception():
    for cls in (ConfigError, FixtureError, SecurityError, UpstreamError,
                LimitExceeded, ValidationFailed, DoctorFailed):
        with pytest.raises(MockRelayError):
            raise cls("x")
