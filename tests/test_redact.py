from mockrelay._07 import _05, _06


def test_01():
    h = {"Authorization": "Bearer abc", "X-Trace": "keep"}
    out = _05(h, ["authorization"])
    assert out["Authorization"] == "{{SECRET}}"
    assert out["X-Trace"] == "keep"


def test_02():
    assert "sk_{{SECRET}}" in _06("key=sk_test_ABC123")
    assert "ghp_{{SECRET}}" in _06("token=ghp_aaaaaaaaaaaaaaaaaaaa")


def test_03_cloud_and_service_keys_are_scrubbed():
    assert "AKIA" + "A" * 16 not in _06("aws AKIA" + "A" * 16)
    assert "AIza" + "a" * 35 not in _06("AIza" + "a" * 35)
    assert "glpat-abcdefghijklmnop" not in _06("glpat-abcdefghijklmnop")
    assert "npm_" + "a" * 30 not in _06("npm_" + "a" * 30)


def test_04_a_private_key_block_is_scrubbed():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIabc\n-----END RSA PRIVATE KEY-----"
    assert "MIIabc" not in _06(text)


def test_05_a_jwt_is_scrubbed():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.sig"
    assert jwt not in _06(jwt)


def test_06_a_token_in_a_query_string_is_scrubbed():
    out = _06("GET /x?access_token=abcdef123&page=2")
    assert "abcdef123" not in out
    assert "page=2" in out


def test_07_a_password_in_a_form_body_is_scrubbed():
    out = _06("password=hunter2&user=alice")
    assert "hunter2" not in out
    assert "user=alice" in out


def test_08_a_database_url_password_is_scrubbed():
    out = _06("postgres://user:s3cret@db.example.com/app")
    assert "s3cret" not in out
    assert "db.example.com" in out


def test_09_an_already_redacted_value_is_not_redacted_twice():
    """A broader pattern must not undo a narrower one that ran first."""
    assert _06("token=ghp_aaaaaaaaaaaaaaaaaaaa") == "token=ghp_{{SECRET}}"
    assert _06(_06("token=ghp_aaaaaaaaaaaaaaaaaaaa")) == "token=ghp_{{SECRET}}"


def test_10_scrubbing_is_idempotent():
    once = _06("auth sk_live_ABC123 and AKIA" + "A" * 16)
    assert _06(once) == once


def test_11_ordinary_text_is_untouched():
    assert _06("a normal message about 3 items") == "a normal message about 3 items"


def test_12_a_nested_structure_is_scrubbed_value_wise():
    from mockrelay._07 import _07 as _value

    out = _value({"a": ["ghp_aaaaaaaaaaaaaaaaaaaa", {"b": "keep"}]})
    assert out["a"][0] == "ghp_{{SECRET}}"
    assert out["a"][1]["b"] == "keep"
