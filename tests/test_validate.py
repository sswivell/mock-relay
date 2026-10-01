"""Fixture validation, which is what makes a broken fixture set a CI failure.

A fixture that cannot be loaded shows up at runtime as a 501 with no
explanation, often in a different repository than the one that recorded
it. Validating the tree up front is what turns that into a line number.

Everything here asserts on the rendered Problem, not on a boolean,
because the value of a validator is entirely in whether the message tells
you what to change.
"""

from __future__ import annotations

import json

import pytest

from mockrelay._18 import _14, _15, _16

SOUND = {
    "id": "gh-get-abc123",
    "upstream": "gh",
    "match": {"method": "GET", "path": "/users/octocat"},
    "request": {
        "method": "GET",
        "path": "/users/octocat",
        "query": {},
        "headers": {},
        "body": None,
    },
    "response": {
        "status": 200,
        "headers": {"content-type": "application/json"},
        "body": {"login": "octocat"},
    },
    "normalize": [],
    "recorded_at": "2024-01-01T00:00:00Z",
    "call_index": 0,
}


def _rendered(problems):
    return [p.render() for p in problems]


def _fields(value):
    return [p.location for p in value]


def _write(tmp_path, name, value):
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _mutate(**changes):
    doc = json.loads(json.dumps(SOUND))
    doc.update(changes)
    return doc


def test_01_a_sound_fixture_produces_no_problems():
    assert _14(SOUND, "f.json") == []


def test_02_a_sound_file_produces_no_problems(tmp_path):
    assert _15(_write(tmp_path, "f.json", SOUND)) == []


def test_03_a_sound_tree_produces_no_problems(tmp_path):
    for name in ("a.json", "sub/b.json"):
        _write(tmp_path, name, SOUND)
    problems, total = _16(tmp_path)
    assert problems == []
    assert total == 0


@pytest.mark.parametrize("value", [[], "text", 7, None, True])
def test_04_a_document_that_is_not_a_mapping_is_reported(value):
    problems = []
    problems = _14(value, "f.json")
    assert problems
    assert "not a mapping" in problems[0].render()


def test_05_a_missing_required_field_is_named():
    doc = _mutate()
    del doc["response"]
    rendered = _rendered(_14(doc, "f.json"))
    assert any("response" in r for r in rendered)


@pytest.mark.parametrize("field", ["id", "upstream", "match", "request", "response"])
def test_06_each_required_field_is_checked(field):
    doc = _mutate()
    del doc[field]
    assert any(field in p.location for p in _14(doc, "f.json"))


def test_07_an_empty_id_is_reported():
    assert any("id" in p.location for p in _14(_mutate(id=""), "f.json"))


def test_08_a_non_string_id_is_reported():
    assert any("not a string" in p.problem for p in _14(_mutate(id=12), "f.json"))


def test_09_an_unknown_top_level_field_is_reported():
    rendered = _rendered(_14(_mutate(colour="blue"), "f.json"))
    assert any("colour" in r for r in rendered)


def test_10_a_match_without_a_path_is_reported():
    doc = _mutate(match={"method": "GET"})
    assert any("path" in p.location for p in _14(doc, "f.json"))


def test_11_a_match_that_is_not_a_mapping_is_reported():
    doc = _mutate(match="GET /x")
    rendered = _rendered(_14(doc, "f.json"))
    assert any("match" in r and "not a mapping" in r for r in rendered)


def test_12_an_unknown_match_field_is_reported():
    doc = _mutate(match={**SOUND["match"], "colour": "blue"})
    assert any("colour" in p.location for p in _14(doc, "f.json"))


def test_13_a_bad_match_mode_is_reported():
    doc = _mutate(match={**SOUND["match"], "match_mode": "sortof"})
    rendered = _rendered(_14(doc, "f.json"))
    assert any("match mode" in r for r in rendered)


def test_14_a_threshold_outside_zero_to_one_is_reported():
    doc = _mutate(match={**SOUND["match"], "fuzzy_threshold": 2.5})
    rendered = _rendered(_14(doc, "f.json"))
    assert any("0.0" in r for r in rendered)


def test_15_a_threshold_that_is_text_is_reported():
    doc = _mutate(match={**SOUND["match"], "fuzzy_threshold": "high"})
    assert any("not a number" in p.problem for p in _14(doc, "f.json"))


def test_16_a_query_subset_value_that_is_not_a_list_is_reported():
    doc = _mutate(match={**SOUND["match"], "query_subset": {"page": 2}})
    rendered = _rendered(_14(doc, "f.json"))
    assert any("query_subset.page" in r for r in rendered)


def test_17_a_non_integer_priority_is_reported():
    doc = _mutate(match={**SOUND["match"], "priority": 1.5})
    assert any("priority" in p.location for p in _14(doc, "f.json"))


def test_18_a_non_boolean_ignore_case_is_reported():
    doc = _mutate(match={**SOUND["match"], "ignore_case": "yes"})
    assert any("ignore_case" in p.location for p in _14(doc, "f.json"))


def test_19_a_request_without_a_method_is_reported():
    doc = _mutate(request={"path": "/x"})
    assert any("method" in p.location for p in _14(doc, "f.json"))


def test_20_a_request_query_that_is_not_a_mapping_is_reported():
    doc = _mutate(request={**SOUND["request"], "query": []})
    rendered = _rendered(_14(doc, "f.json"))
    assert any("request.query" in r for r in rendered)


def test_21_an_unknown_request_field_is_reported():
    doc = _mutate(request={**SOUND["request"], "colour": "blue"})
    assert any("colour" in p.location for p in _14(doc, "f.json"))


def test_22_a_response_without_a_status_is_reported():
    doc = _mutate(response={"headers": {}, "body": None})
    assert any("status" in p.location for p in _14(doc, "f.json"))


@pytest.mark.parametrize("status", [0, 99, 600, 1000, -200])
def test_23_a_status_outside_http_range_is_reported(status):
    doc = _mutate(response={**SOUND["response"], "status": status})
    rendered = _rendered(_14(doc, "f.json"))
    assert any("100 and 599" in r for r in rendered)


@pytest.mark.parametrize("status", [100, 200, 301, 404, 500, 599])
def test_24_a_status_inside_http_range_is_accepted(status):
    doc = _mutate(response={**SOUND["response"], "status": status})
    assert _14(doc, "f.json") == []


def test_25_a_status_that_is_text_is_reported():
    doc = _mutate(response={**SOUND["response"], "status": "200"})
    assert any("status" in p.location for p in _14(doc, "f.json"))


def test_26_a_response_that_is_not_a_mapping_is_reported():
    doc = _mutate(response=[200])
    rendered = _rendered(_14(doc, "f.json"))
    assert any("response" in r and "not a mapping" in r for r in rendered)


def test_27_a_normalize_that_is_not_a_list_is_reported():
    doc = _mutate(normalize="$.id")
    assert any("normalize" in p.location for p in _14(doc, "f.json"))


def test_28_a_non_string_recorded_at_is_reported():
    doc = _mutate(recorded_at=0)
    assert any("recorded_at" in p.location for p in _14(doc, "f.json"))


def test_29_a_missing_call_index_is_fine():
    doc = _mutate()
    del doc["call_index"]
    assert _14(doc, "f.json") == []


def test_30_a_file_that_is_not_json_is_reported(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    problems = _15(path)
    assert len(problems) == 1
    assert "not valid JSON" in problems[0].render()
    assert "broken.json" in problems[0].render()


def test_31_an_unreadable_file_is_reported(tmp_path, monkeypatch):
    path = _write(tmp_path, "f.json", SOUND)
    monkeypatch.setattr(
        type(path),
        "read_text",
        lambda self, *a, **k: (_ for _ in ()).throw(PermissionError(13, "denied")),
    )
    problems = _15(path)
    assert problems
    assert "could not be read" in problems[0].render()


def test_32_a_tree_reports_every_broken_file(tmp_path):
    _write(tmp_path, "good.json", SOUND)
    _write(tmp_path, "bad.json", {"id": "x"})
    (tmp_path / "garbage.json").write_text("nope", encoding="utf-8")
    problems, total = _16(tmp_path)
    assert total == len(problems)
    assert len(problems) >= 2
    rendered = " ".join(_rendered(problems))
    assert "bad.json" in rendered
    assert "garbage.json" in rendered


def test_33_a_missing_tree_is_reported_once(tmp_path):
    problems, total = _16(tmp_path / "absent")
    assert total == 1
    assert "does not exist" in problems[0].render()


def test_34_a_tree_that_is_a_file_is_reported(tmp_path):
    path = tmp_path / "f.json"
    path.write_text("{}", encoding="utf-8")
    problems, total = _16(path)
    assert total == 1
    assert "not a directory" in problems[0].render()


def test_35_the_number_of_reported_problems_is_capped(tmp_path):
    """A thousand broken fixtures must not become a thousand-line report."""
    for i in range(12):
        _write(tmp_path, f"bad-{i}.json", {"id": str(i)})
    problems, total = _16(tmp_path, limit=3)
    assert len(problems) <= 3
    assert total > len(problems)


def test_36_an_empty_tree_is_valid(tmp_path):
    problems, total = _16(tmp_path)
    assert (problems, total) == ([], 0)
