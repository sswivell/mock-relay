"""The admin dashboard must never execute data it renders.

The dashboard builds its tables from `/api/recent` and `/api/fixtures`.
Both carry attacker-supplied strings: the request path of anything that
reached the proxy, and the recorded path of any fixture. Interpolating
those into `innerHTML` made the admin port a stored-XSS delivery
mechanism against whoever opened it, which in the documented setup is
the developer running the mock.

The page must build cells with `textContent`. This is a source-level
assertion, not a browser test: there is no DOM here, so what it checks is
that no template literal of untrusted data is left on the page.
"""

import pytest

from mockrelay._14 import _04 as PAGE

XSS_PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "'\"><svg/onload=alert(1)>",
    "</td></tr><script>alert(document.domain)</script>",
    "javascript:alert(1)",
    "${alert(1)}",
    "{{7*7}}",
    "`+alert(1)+`",
]


def test_01_the_page_exists_and_is_html():
    assert PAGE.lstrip().startswith("<!doctype html>")
    assert "<script>" in PAGE


def test_02_no_innerhtml_sink_survives_anywhere_in_the_page():
    """The whole bug in one assertion.

    Even `el.innerHTML = ''` is gone, replaced by replaceChildren(), so
    there is no sink left for a future edit to reach for by muscle
    memory.
    """
    assert "innerHTML" not in PAGE
    assert "outerHTML" not in PAGE
    assert "insertAdjacentHTML" not in PAGE
    assert "document.write" not in PAGE


def test_03_no_template_literal_reaches_an_html_sink():
    """`${...}` must never appear inside markup in this page."""
    for i, line in enumerate(PAGE.splitlines(), 1):
        stripped = line.strip()
        if "${" not in stripped:
            continue
        # The one legitimate use is building the style attribute, which is
        # authored, not fetched. Nothing else may interpolate.
        assert "background:" not in stripped and "body{" not in stripped, (
            f"line {i} interpolates into markup: {stripped}")
    # And in the script block proper there must be no template literals.
    script = PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
    assert "`" not in script, "the script block still builds markup from strings"


def test_04_cells_are_written_with_textcontent():
    script = PAGE.split("<script>", 1)[1].split("</script>", 1)[0]
    assert "textContent" in script
    # At least as many assignments as there are user-facing columns.
    assert script.count("textContent") >= 8, script


def test_05_the_static_shell_still_uses_the_known_good_id_globals():
    """The header cells rely on named globals; keep them working."""
    for el in ("mode", "lat", "hits", "miss", "rec"):
        assert f'id="{el}"' in PAGE, el


@pytest.mark.parametrize("payload", XSS_PAYLOADS)
def test_06_a_payload_in_a_dashboard_column_has_nothing_to_escape_into(payload):
    """Documents the payloads and why textContent neutralises them.

    With textContent the string is written as a text node, so `<`, `>`
    and `&` are escaped by the DOM and no element or attribute is ever
    created from the data. This test cannot run a DOM, so it asserts the
    structural precondition: the page has no sink that a payload could
    reach.
    """
    assert "innerHTML" not in PAGE
    assert "outerHTML" not in PAGE
    assert "insertAdjacentHTML" not in PAGE
    assert "document.write" not in PAGE
    # Sanity: each payload carries at least one character that matters in
    # a markup, template-literal, or URL context, so the cases are not
    # vacuous.
    assert set(payload) & set("<>${}`'\":()")


def test_07_the_page_has_no_template_literals_in_the_script_block():
    script = script_of(PAGE)
    assert "`" not in script
    assert "${" not in script


def script_of(page: str) -> str:
    return page.split("<script>", 1)[1].split("</script>", 1)[0]
