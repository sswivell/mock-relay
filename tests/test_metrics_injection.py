"""Prometheus exposition must survive a hostile label value.

`/metrics` is unauthenticated and the request path it reports is copied
verbatim from the request target. Prometheus label values are delimited by
double quotes and may not contain an unescaped quote, backslash or
newline, so a path containing one of those would close the label early
and let the remainder be parsed as extra labels, a second series, or an
entirely new metric line.

The assertions below are parser-level and need no Prometheus client: every
emitted line is matched against the text-format grammar for a sample.
"""

import re

import pytest

from mockrelay._11 import _01 as Metrics
from mockrelay._11 import _10 as escape

_COMMENT = re.compile(r"^# (HELP|TYPE) [a-zA-Z_:][a-zA-Z0-9_]* .*$")
_LABEL_VALUE = r'(?:[^"\\\n]|\\.)*'
_LABEL = r'[a-zA-Z_][a-zA-Z0-9_]*="' + _LABEL_VALUE + r'"'
_SAMPLE = re.compile(
    r"^([a-zA-Z_:][a-zA-Z0-9_]*)\{(" + _LABEL + r"(?:," + _LABEL + r")*)\}"
    r" (-?[0-9]+(?:\.[0-9]+)?)$"
)

INJECTIONS = [
    '"} fake_metric_total{a="1',
    '"} 999\n# HELP pwned',
    '"} injected{a="\\',
    'a\\"b',
    'line1\nline2',
    'carriage\rreturn',
    '}}} {key="shadow',
    "\x00null",
    "back\\\\slash",
    '"} 1\nmockrelay_fake_total 1',
    '","other="1',
]


def _series(text):
    return [ln for ln in text.splitlines() if ln and not ln.startswith("#")]


_LABEL_NAME = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)="' + _LABEL_VALUE + r'"')


def _label_names(line):
    """Label names in an emitted sample, ignoring anything inside values."""
    body = _SAMPLE.match(line).group(2)
    return [m.group(1) for m in _LABEL_NAME.finditer(body)]


def _assert_valid(text, why=""):
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith("#"):
            assert _COMMENT.match(line), (why, line)
        else:
            assert _SAMPLE.match(line), (why, line)
    return text


@pytest.mark.parametrize("raw", INJECTIONS)
def test_01_escaping_removes_every_illegal_character(raw):
    out = escape(raw)
    body = out.replace(r"\\", "").replace(r"\"", "").replace(r"\n", "")
    body = body.replace(r"\r", "")
    assert '"' not in body, out
    assert "\n" not in body and "\r" not in body, out


@pytest.mark.parametrize("raw", INJECTIONS)
def test_02_the_whole_exposition_still_parses(raw):
    m = Metrics()
    m._06(f'gh GET /x{raw}', 200, "replay")
    _assert_valid(m._08(), raw)


@pytest.mark.parametrize("raw", INJECTIONS)
def test_03_a_hostile_path_adds_no_series_and_no_label(raw):
    m = Metrics()
    m._06(f'gh GET /x{raw}', 200, "replay")
    text = m._08()
    series = _series(text)
    assert len(series) == 3, (raw, series)
    assert _label_names(series[0]) == ["key"], (raw, series[0])
    assert _label_names(series[1]) == ["key"], (raw, series[1])
    assert _label_names(series[2]) == ["mode"], (raw, series[2])


@pytest.mark.parametrize("raw", INJECTIONS)
def test_04_a_hostile_path_keeps_the_value_as_one_label(raw):
    m = Metrics()
    m._06(f'gh GET /x{raw}', 200, "replay")
    line = _series(m._08())[0]
    value = _SAMPLE.match(line).group(2)
    assert value.startswith('key="gh GET /x')


def test_05_a_hostile_mode_value_is_escaped_too():
    m = Metrics()
    m._06("k", 200, 're"} fake_total 1\n# HELP injected')
    text = _assert_valid(m._08())
    assert len(_series(text)) == 3, _series(text)


def test_06_a_hostile_value_in_every_counter():
    m = Metrics()
    m._06('k"} 5', 200, 'm"} 7')
    _assert_valid(m._08())


def test_07_ordinary_values_are_untouched():
    m = Metrics()
    m._06("gh GET /users/7", 200, "replay")
    text = m._08()
    assert 'mockrelay_requests_total{key="gh GET /users/7"} 1' in text
    assert 'mockrelay_responses_total{key="gh GET /users/7:200"} 1' in text
    assert 'mockrelay_mode_total{mode="replay"} 1' in text
    _assert_valid(text)


def test_08_the_output_ends_with_a_newline():
    m = Metrics()
    m._06("k", 200, "replay")
    assert m._08().endswith("\n")


def test_09_backslashes_are_escaped_before_quotes():
    """Order matters: doubling quotes first would double the backslashes."""
    assert escape('a"b') == r'a\"b'
    assert escape("a\\b") == r"a\\b"
    assert escape('a\\"b') == r'a\\\"b'
    assert escape("a\nb") == r"a\nb"


def test_10_an_empty_value_is_legal():
    m = Metrics()
    m._06("", 200, "")
    _assert_valid(m._08())


def test_11_a_unicode_path_survives():
    m = Metrics()
    m._06("gh GET /café/über", 200, "replay")
    text = _assert_valid(m._08())
    assert "café" in text
