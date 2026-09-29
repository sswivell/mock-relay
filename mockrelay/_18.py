"""Validation: load a config and a fixture tree, and describe what is wrong.

`validate` exists so a broken fixture set fails a CI step with a message
that names the file and the field, rather than surfacing as a 501 at
runtime in the middle of a test suite. Everything here returns Problems
instead of raising, for the same reason: the point is to list all of the
faults at once, not to stop at the first one.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import Problem

MAX_REPORTED = 100

_REQUIRED = ("id", "upstream", "match", "request", "response")
_MATCH_KEYS = ("method", "path", "query_subset", "body_contains", "match_mode",
               "fuzzy_threshold", "ignore_case", "priority")
_REQUEST_KEYS = ("method", "path", "query", "headers", "body")
_RESPONSE_KEYS = ("status", "headers", "body")


def _04(value: Any, keys: tuple[str, ...], where: str,
        problems: list[Problem]) -> None:
    extra = [k for k in value if k not in keys]
    for key in extra:
        problems.append(Problem(
            "is not a fixture field and would be ignored",
            expected="one of " + ", ".join(keys),
            location=f"{where}.{key}",
        ))


def _05(value: Any, required: tuple[str, ...], allowed: tuple[str, ...],
        where: str, problems: list[Problem]) -> bool:
    """Check one nested mapping: present, complete, and free of strays."""
    if not isinstance(value, dict):
        problems.append(Problem(
            f"is a {type(value).__name__}, not a mapping", location=where))
        return False
    for key in required:
        if key not in value:
            problems.append(Problem(
                "is missing", expected=f"a {key} field", location=f"{where}.{key}"))
    _04(value, allowed, where, problems)
    return all(k in value for k in required)


def _06(value: Any, where: str, problems: list[Problem]) -> None:
    if value is not None and not isinstance(value, str):
        problems.append(Problem("is not a string", location=where))


def _07(value: Any, where: str, problems: list[Problem]) -> None:
    if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
        problems.append(Problem("is not a whole number", location=where))


def _08(value: Any, where: str, problems: list[Problem]) -> None:
    if value is not None and not isinstance(value, dict):
        problems.append(Problem("is not a mapping", location=where))


def _09(value: Any, where: str, problems: list[Problem]) -> None:
    if value is not None and not isinstance(value, bool):
        problems.append(Problem("is not true or false", location=where))


def _10(value: Any, where: str, problems: list[Problem]) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append(Problem("is not a number", location=where))
    elif not 0.0 <= float(value) <= 1.0:
        problems.append(Problem(
            "is outside 0.0 - 1.0", expected="a similarity threshold",
            location=where))


def _11(match: dict[str, Any], where: str, problems: list[Problem]) -> None:
    if not _05(match, ("method", "path"), _MATCH_KEYS, where, problems):
        return
    _06(match["method"], f"{where}.method", problems)
    _06(match["path"], f"{where}.path", problems)
    _08(match.get("query_subset"), f"{where}.query_subset", problems)
    _06(match.get("match_mode"), f"{where}.match_mode", problems)
    _07(match.get("priority"), f"{where}.priority", problems)
    _09(match.get("ignore_case"), f"{where}.ignore_case", problems)
    _10(match.get("fuzzy_threshold"), f"{where}.fuzzy_threshold", problems)
    mode = match.get("match_mode")
    if mode is not None and mode not in ("auto", "exact", "wildcard",
                                         "regex", "fuzzy"):
        problems.append(Problem(
            "is not a recognised match mode",
            expected="auto, exact, wildcard, regex or fuzzy",
            location=f"{where}.match_mode"))
    rows = match.get("query_subset")
    if isinstance(rows, dict):
        for key, value in rows.items():
            if not isinstance(value, list):
                problems.append(Problem(
                    "is not a list of expected values",
                    expected=f"{key}: ['one', 'two']",
                    location=f"{where}.query_subset.{key}"))


def _12(request: dict[str, Any], where: str, problems: list[Problem]) -> None:
    if not _05(request, ("method", "path"), _REQUEST_KEYS, where, problems):
        return
    _06(request["method"], f"{where}.method", problems)
    _06(request["path"], f"{where}.path", problems)
    _08(request.get("query"), f"{where}.query", problems)
    _08(request.get("headers"), f"{where}.headers", problems)


def _13(response: dict[str, Any], where: str, problems: list[Problem]) -> None:
    if not _05(response, ("status",), _RESPONSE_KEYS, where, problems):
        return
    status = response["status"]
    if isinstance(status, bool) or not isinstance(status, int):
        problems.append(Problem(
            "is not an HTTP status", location=f"{where}.status"))
    elif not 100 <= status <= 599:
        problems.append(Problem(
            "is outside the range of HTTP status codes",
            expected="a status between 100 and 599",
            location=f"{where}.status"))
    _08(response.get("headers"), f"{where}.headers", problems)


def _14(value: Any, where: str) -> list[Problem]:
    """Validate a parsed fixture document; returns the problems found."""
    problems: list[Problem] = []
    if not isinstance(value, dict):
        problems.append(Problem(
            f"is a {type(value).__name__}, not a mapping",
            expected="a recorded fixture document", location=where))
        return problems
    missing = [k for k in _REQUIRED if k not in value]
    for key in missing:
        problems.append(Problem(
            "is missing", expected=f"a {key} field", location=f"{where}.{key}"))
    if missing:
        return problems
    _06(value["id"], f"{where}.id", problems)
    _06(value["upstream"], f"{where}.upstream", problems)
    if isinstance(value["id"], str) and not value["id"]:
        problems.append(Problem(
            "is empty", expected="a non-empty fixture id", location=f"{where}.id"))
    if isinstance(value["match"], dict):
        _11(value["match"], f"{where}.match", problems)
    else:
        problems.append(Problem(
            "is not a mapping", location=f"{where}.match"))
    if isinstance(value["request"], dict):
        _12(value["request"], f"{where}.request", problems)
    else:
        problems.append(Problem(
            "is not a mapping", location=f"{where}.request"))
    if isinstance(value["response"], dict):
        _13(value["response"], f"{where}.response", problems)
    else:
        problems.append(Problem(
            "is not a mapping", location=f"{where}.response"))
    normalize = value.get("normalize")
    if normalize is not None and not isinstance(normalize, list):
        problems.append(Problem("is not a list", location=f"{where}.normalize"))
    _07(value.get("call_index"), f"{where}.call_index", problems)
    _06(value.get("recorded_at"), f"{where}.recorded_at", problems)
    for key in value:
        if key not in (*_REQUIRED, "normalize", "recorded_at", "call_index"):
            problems.append(Problem(
                "is not a fixture field and would be ignored",
                location=f"{where}.{key}"))
    return problems


def _15(path: Path) -> list[Problem]:
    """Validate one fixture file on disk."""
    where = str(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        return [Problem(f"could not be read: {e.strerror or e}",
                        expected="a readable fixture file", location=where)]
    try:
        data = json.loads(text)
    except ValueError as e:
        return [Problem(f"is not valid JSON: {e}", location=where)]
    return _14(data, where)


def _16(root: Path, limit: int = MAX_REPORTED) -> tuple[list[Problem], int]:
    """Validate every fixture under *root*.

    Returns the problems to show and the total found, so a caller can say
    how many were withheld rather than printing thousands of them.
    """
    root = Path(root)
    if not root.exists():
        return [Problem("does not exist",
                        expected="a directory of recorded fixtures",
                        location=str(root))], 1
    if not root.is_dir():
        return [Problem("is not a directory",
                        expected="a directory of recorded fixtures",
                        location=str(root))], 1
    problems: list[Problem] = []
    total = 0
    for path in sorted(root.rglob("*.json")):
        found = _15(path)
        total += len(found)
        if len(problems) < limit:
            problems.extend(found[:limit - len(problems)])
    return problems, total
