"""Content-Length is a promise about framing, so it has to be parsed strictly.

The proxy reads the body with `int(self.headers.get("Content-Length", 0))`.
`int()` accepts far more than HTTP does: it takes a leading `+`, it accepts
surrounding whitespace, and it parses `0x10` only by accident of raising.
A negative value is worse than a crash, because `rfile.read(-5)` does not
fail -- it reads to end of stream, so the request is framed by whatever
the client sent next.

Every accepted shape is listed below with the reason it is or is not legal.
The test asserts the exact integer, not merely that nothing raised, so a
lenient regression is visible.
"""

import pytest

from mockrelay.security import parse_content_length

# Values HTTP permits: a run of decimal digits.
VALID = [
    ("0", 0),
    ("1", 1),
    ("9", 9),
    ("10", 10),
    ("000", 0),
    ("007", 7),
    ("1234567890", 1234567890),
]

# Values HTTP does not permit. Each is a case where leniency is a bug.
INVALID = [
    "",            # present but empty
    " ",           # whitespace only
    "abc",
    "-1",          # negative: read(-1) reads to EOF, silently reframing
    "-0",
    "+5",          # int() accepts this; HTTP does not
    " 5 ",         # int() strips this; a proxy must not guess
    "5 ",          # trailing OWS
    " 5",
    "5.0",         # not an integer
    "1e3",         # scientific notation
    "0x10",        # hexadecimal
    "5, 5",        # comma-joined, as proxies have historically emitted
    "5;5",
    "999999999999999999999999",   # beyond any integer width we would honour
    "5\n",         # header injection attempt
    "5\r\n",
    "0b101",
    "0o17",
    "５",           # fullwidth digit: int() accepts it
    "1_000",       # underscore separators: int() accepts it
]


@pytest.mark.parametrize("raw,expected", VALID)
def test_01_legal_values_parse_to_the_declared_length(raw, expected):
    assert parse_content_length(raw) == expected


@pytest.mark.parametrize("raw", INVALID)
def test_02_illegal_values_are_refused(raw):
    from mockrelay.errors import SecurityError

    with pytest.raises(SecurityError) as e:
        parse_content_length(raw)
    assert "Content-Length" in str(e.value)


def test_03_absent_is_zero_and_distinguishable_from_present_but_empty():
    """`None` means no header; `""` means a header with no value."""
    assert parse_content_length(None) == 0
    with pytest.raises(Exception):
        parse_content_length("")


def test_04_leading_zeros_do_not_change_the_value():
    assert parse_content_length("0000000005") == 5
    assert parse_content_length("0") == 0


def test_05_a_very_long_digit_run_is_refused_rather_than_truncated():
    """No legitimate body is 100 digits long; a DoS probe often is."""
    from mockrelay.errors import SecurityError

    with pytest.raises(SecurityError):
        parse_content_length("1" * 100)
    assert parse_content_length("1" * 18) == int("1" * 18)


def test_06_the_value_is_not_accepted_as_bool_or_int_by_accident():
    """The parser takes the raw header string, not a pre-coerced value."""
    assert parse_content_length(5) == 5
    assert parse_content_length(b"5") == 5


def test_07_only_digits_are_ever_accepted():
    """Whitelist, not blacklist: a new character class cannot slip in."""
    import string

    from mockrelay.errors import SecurityError

    for ch in string.printable:
        if ch in string.digits:
            continue
        with pytest.raises(SecurityError):
            parse_content_length("5" + ch)
