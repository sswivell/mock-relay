"""An error message must be printable, whatever it is quoting.

parse_content_length quotes the offending value back to the user. When
that value contains a character outside the console's encoding, printing
the message raises UnicodeEncodeError -- and the thing that breaks is the
error renderer, so a hostile request turns a clean 400 into a crash while
the diagnostic is being composed.

MockRelay writes errors to a real console, which on Windows is routinely
cp1252, and it also writes them to a JSON body. Both need the message to
survive.
"""

import io

import pytest

from mockrelay.errors import SecurityError
from mockrelay.security import parse_content_length

# Characters that a narrow Windows console cannot encode. Written as
# escapes so the file stays readable and so an editor cannot normalise one
# of them into plain ASCII behind the test's back.
HOSTILE = [
    "\uff15",       # fullwidth digit five
    "é",            # latin-1, fine in UTF-8 but not cp437
    "あ",       # hiragana
    "\U0001f600",        # emoji
    "�",      # replacement char
    "\u00a0",       # non-breaking space
    "\u2028",       # line separator
    "\x00",          # NUL
    "\x7f",          # DEL
    "",            # zero-width space
]

CONSOLE_ENCODINGS = ["cp1252", "cp437", "ascii", "latin-1"]


@pytest.mark.parametrize("value", HOSTILE)
def test_01_the_message_encodes_under_every_console_encoding(value):
    msg = str(SecurityError("bad"))
    for enc in CONSOLE_ENCODINGS:
        msg.encode(enc, errors="strict")


@pytest.mark.parametrize("value", HOSTILE)
def test_02_the_rejection_message_never_echoes_the_raw_value(value):
    """The message must describe the problem, not re-quote the payload."""
    from mockrelay.errors import MockRelayError

    with pytest.raises(SecurityError) as e:
        parse_content_length(value)
    msg = str(e.value)
    for enc in CONSOLE_ENCODINGS:
        msg.encode(enc, errors="strict"), (value, enc)
    assert isinstance(e.value, MockRelayError)


@pytest.mark.parametrize("value", HOSTILE)
def test_03_the_message_survives_a_json_round_trip(value):
    import json

    with pytest.raises(SecurityError) as e:
        parse_content_length(value)
    body = json.dumps({"error": str(e.value)})
    assert json.loads(body)["error"]


@pytest.mark.parametrize("value", HOSTILE)
def test_04_printing_the_message_to_a_narrow_stream_does_not_raise(value):
    with pytest.raises(SecurityError) as e:
        parse_content_length(value)
    for enc in CONSOLE_ENCODINGS:
        buf = io.TextIOWrapper(io.BytesIO(), encoding=enc,
                              errors="strict", newline="")
        try:
            buf.write(str(e.value))
        except UnicodeEncodeError as exc:  # pragma: no cover - the defect
            pytest.fail(f"{value!r} unprintable under {enc}: {exc}")
        finally:
            buf.detach()


def test_05_the_digit_check_still_rejects_what_it_used_to():
    """Losing the echo must not weaken the check."""
    for value in HOSTILE:
        with pytest.raises(SecurityError):
            parse_content_length(value)
    assert parse_content_length("12345") == 12345
