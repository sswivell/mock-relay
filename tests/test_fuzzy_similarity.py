"""A shared prefix is not a near-miss.

_20 is the similarity behind fuzzy matching. Its size guard refuses to run
difflib over pairs whose lengths multiply past 250000, because difflib is
quadratic and an untrusted request body can be arbitrarily large. The guard
answered that refusal with 1.0 whenever one string started with the other,
but 1.0 is not a similarity score, it is a claim of identity, and matching
treats it as one: a path and that path plus "-archive" scored the same as a
string and its own copy.

The guard is right, the answer was wrong, and it only fires for inputs over
roughly 500x500 characters, which is why it survived review. Every pair
below is built long in the first place so that it reaches the guard with
its prefix relation intact. Padding a short pair afterwards cannot work:
the filler lands after the point of divergence, and padding both sides
with the same filler collapses "/users" and "/usersx" into one string, so
the test ends up asserting that a string is not equal to itself.
"""

import pytest

from mockrelay._09 import _07, _12, _20

GUARD = 250000  # the length product _20 refuses to run difflib over

# A shared stem long enough that every pair built from it clears GUARD:
# 828 * 828 is 685584.
STEM = "/api/v1/" + "teams/" * 90

# Pairs where one side really is a prefix of the other.
PREFIX_PAIRS = [
    (STEM, STEM + "users"),
    (STEM + "users", STEM + "users-archive"),
    ("x" * 600, "x" * 601),
    ("x" * 600, "x" * 600 + "y"),
    ("/api/v1/users/" + "deep/" * 110, "/api/v1/users/" + "deep/" * 110 + "x"),
]
PREFIX_IDS = ["stem", "suffix", "one-longer", "trailing-char", "deep-path"]


def _product(a: str, b: str) -> int:
    return len(a) * len(b)


# The bug itself.


@pytest.mark.parametrize("a,b", PREFIX_PAIRS, ids=PREFIX_IDS)
def test_01_a_long_shared_prefix_is_not_a_perfect_score(a, b):
    assert _product(a, b) > GUARD, "pair does not reach the size guard"
    assert _20(a, b) < 1.0


@pytest.mark.parametrize("a,b", PREFIX_PAIRS, ids=PREFIX_IDS)
def test_02_a_long_shared_prefix_never_meets_a_strict_threshold(a, b):
    """The consequence that matters: threshold=1.0 has to mean exact."""
    opts = _07(threshold=1.0, fuzzy_enabled=True)
    assert _20(a, b) < opts.threshold
    assert _12(a, b, opts, "fuzzy") is None


@pytest.mark.parametrize("a,b", PREFIX_PAIRS, ids=PREFIX_IDS)
def test_03_a_long_shared_prefix_still_matches_a_sane_threshold(a, b):
    """The fix must not collapse into "large strings never match".

    A near miss on a long path is still a near miss. Routing a request for
    /api/v1/users to a fixture recorded for that path is the whole point of
    fuzzy matching, and it has to keep working past the size guard.
    """
    assert _20(a, b) >= 0.86
    assert _12(a, b, _07(mode="fuzzy"), "fuzzy") == 100


# The shape of the number the guard now returns.


@pytest.mark.parametrize("a,b", PREFIX_PAIRS, ids=PREFIX_IDS)
def test_04_the_guard_scores_by_how_much_of_the_longer_string_is_shared(a, b):
    short, long = sorted((a, b), key=len)
    assert _20(a, b) == pytest.approx(len(short) / len(long))


def test_05_a_longer_tail_scores_lower():
    """The ranking the store sorts on has to stay monotonic."""
    near = _20(STEM, STEM + "users")
    mid = _20(STEM, STEM + "users" * 10)
    far = _20(STEM, STEM + "users" * 1000)
    assert near > mid > far > 0.0


def test_06_unrelated_long_strings_stay_at_zero():
    assert _20("a" * 600, "b" * 600) == 0.0
    assert _20(STEM, "z" * len(STEM)) == 0.0
    # Differing at the very first character is as far apart as strings get.
    assert _20("a" + "x" * 600, "b" + "y" * 600) == 0.0


def test_07_the_guard_never_calls_a_real_prefix_zero():
    a, b = STEM, STEM + "users"
    assert 0.0 < _20(a, b) < 1.0


# Invariants that must hold for every input shape.


@pytest.mark.parametrize("a,b", PREFIX_PAIRS, ids=PREFIX_IDS)
def test_08_the_score_is_symmetric(a, b):
    assert _20(a, b) == _20(b, a)


def test_09_identical_strings_are_perfect_at_any_size():
    for s in ("", "a", "x" * 499, "x" * 500, "x" * 501, STEM, STEM * 4):
        assert _20(s, s) == 1.0
        assert _20(s, s[:]) == 1.0
        assert _20(s[:], s) == 1.0


def test_10_the_score_never_leaves_the_unit_interval():
    pairs = (*PREFIX_PAIRS, ("", "abc"), ("abc", ""), ("", ""))
    for a, b in pairs:
        assert 0.0 <= _20(a, b) <= 1.0
        assert 0.0 <= _20(b, a) <= 1.0


def test_11_empty_strings_score_zero_against_anything_real():
    assert _20("", "") == 1.0
    assert _20("", "abc") == 0.0
    assert _20("abc", "") == 0.0
    assert _20("", STEM) == 0.0
    assert _20(STEM, "") == 0.0


def test_12_the_short_string_case_is_untouched():
    """difflib still answers below the guard, prefix or not."""
    pairs = [
        ("/api/v1/users", "/api/v1/users-archive"),
        ("/api/v1/users", "/api/v1/usersx"),
        ("/a" * 100, "/a" * 99 + "b"),
        ("/v1/resource", "/v1/resource-collection"),
        (
            "/very/long/shared/prefix/for/two/paths",
            "/very/long/shared/prefix/for/two/pathsx",
        ),
    ]
    for a, b in pairs:
        assert _product(a, b) <= GUARD, (a, b)
        assert _20(a, b) < 1.0, (a, b)
        assert _20(a, b) == _20(b, a), (a, b)
    # difflib is stricter than the guard about short prefixes, because it
    # charges for the unmatched tail on both sides. That difference is the
    # cost of not running it, and it is one directional: the guard is the
    # more generous of the two, never the stricter.
    assert _20("/api/v1/users", "/api/v1/users-archive") < 0.86
    assert _20("/api/v1/users", "/api/v1/users-archive") < _20(
        *sorted((STEM, STEM + "users"), key=len)
    )


# The boundary the guard sits on.


def test_13_the_two_paths_disagree_on_value_and_agree_on_property():
    """499x501 is the last product under the guard, 500x501 the first over.

    Both sides must keep the property that matters and differ only in the
    exact number, which is what says the boundary is where the code says
    it is.
    """
    under_a, under_b = "a" * 499, "a" * 501
    over_a, over_b = "a" * 500, "a" * 501
    assert _product(under_a, under_b) == 249999 <= GUARD  # difflib
    assert _product(over_a, over_b) == 250500 > GUARD  # the guard

    for a, b in ((under_a, under_b), (over_a, over_b)):
        assert a != b
        assert 0.0 < _20(a, b) < 1.0
        assert _20(a, b) == _20(b, a)

    # difflib counts the matching block twice; the guard counts it once.
    assert _20(under_a, under_b) == pytest.approx(2 * 499 / 1000)
    assert _20(over_a, over_b) == pytest.approx(500 / 501)


def test_14_the_boundary_holds_for_unrelated_long_strings_too():
    assert _20("a" * 500, "b" * 500) == 0.0
    assert _20("a" * 500, "b" * 501) == 0.0
