"""Exception types, exit codes, and user-facing error rendering.

Every failure a user can cause should arrive as one of these, not as a
traceback. Each carries enough structure to point at the file and the setting
that is wrong, and to say what was expected instead.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

__all__ = [
    "EXIT_CONFIG",
    "EXIT_DOCTOR",
    "EXIT_ERROR",
    "EXIT_INTERRUPTED",
    "EXIT_OK",
    "EXIT_USAGE",
    "EXIT_VALIDATION",
    "ConfigError",
    "ConfigLoadError",
    "DoctorFailed",
    "ExitCode",
    "FixtureError",
    "FixtureSchemaError",
    "FramingError",
    "LimitExceeded",
    "MockRelayError",
    "Problem",
    "SecurityError",
    "StoreError",
    "UpstreamError",
    "ValidationFailed",
    "as_problems",
    "render_problems",
]

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_CONFIG = 3
EXIT_VALIDATION = 4
EXIT_DOCTOR = 5
EXIT_INTERRUPTED = 130

ExitCode = int


class Problem:
    """One concrete, actionable defect."""

    __slots__ = ("expected", "location", "problem", "subject")

    def __init__(
        self, problem: str, subject: str = "", expected: str = "", location: str = ""
    ) -> None:
        self.problem = problem
        self.subject = subject
        self.expected = expected
        self.location = location

    def as_dict(self) -> dict:
        out = {"problem": self.problem}
        for key in ("subject", "expected", "location"):
            value = getattr(self, key)
            if value:
                out[key] = value
        return out

    def render(self) -> str:
        head = self.problem
        if self.subject and self.subject not in head:
            head = f"{self.subject} {head}"
        out = head
        if self.expected:
            out += f"\nExpected: {self.expected}"
        if self.location:
            out += f"\n  at: {self.location}"
        return out

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Problem({self.render()!r})"


UNKNOWN_PROBLEM = "the problem was not described"


def as_problems(value):
    """Accept a bare string, one ``Problem``, or any iterable of them.

    Call sites almost always have a single message in hand, and forcing them
    to construct a ``Problem`` just to raise would be noise. An empty
    iterable is an error in its own right, so it reports as such rather than
    rendering an empty section.
    """
    if isinstance(value, Problem):
        return [value]
    if isinstance(value, str):
        return [Problem(value)] if value else [Problem(UNKNOWN_PROBLEM)]
    if not isinstance(value, Iterable):
        return [Problem(str(value))]
    items = [v if isinstance(v, Problem) else Problem(str(v)) for v in value]
    return items or [Problem(UNKNOWN_PROBLEM)]


def render_problems(
    kind: str,
    problems: Sequence[Problem],
    source: str = "",
    hint: str = "",
    limit: int = 0,
) -> str:
    from ._07 import _06 as scrub

    lines: list[str] = [kind, ""]
    if source:
        lines.append("File:")
        lines.append("  " + source)
        lines.append("")
    lines.append("Problem:")
    problems = as_problems(problems)
    shown = list(problems) if limit <= 0 else list(problems)[:limit]
    for i, p in enumerate(shown):
        text = scrub(p.render())
        lines.append(text if i == 0 else "  " + text.replace("\n", "\n  "))
    extra = len(problems) - len(shown)
    if extra > 0:
        lines.append("")
        lines.append(f"  ... and {extra} more problem(s)")
    if hint:
        lines.append("")
        lines.append("Next:")
        lines.append("  " + hint)
    return "\n".join(lines)


class MockRelayError(Exception):
    """Base class for every error MockRelay raises on purpose."""

    exit_code: ExitCode = EXIT_ERROR
    kind = "Error"
    #: Stable machine-readable token, safe to switch on in a client.
    #: Unlike `kind`, which is a human-readable phrase and may be reworded.
    code = "error"

    def __init__(
        self,
        message: str = "",
        source: str = "",
        hint: str = "",
        exit_code: ExitCode | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.source = source
        self.hint = hint
        if exit_code is not None:
            self.exit_code = exit_code

    def render(self) -> str:
        from ._07 import _06 as scrub

        return render_problems(
            f"{self.kind}",
            [Problem(scrub(self.message))],
            source=self.source,
            hint=self.hint,
        )


class ConfigError(MockRelayError):
    exit_code = EXIT_CONFIG
    kind = "Configuration error"
    code = "config"

    def __init__(
        self,
        problems: Iterable[Problem],
        source: str = "",
        hint: str = "",
        exit_code: ExitCode | None = None,
    ) -> None:
        self.problems = as_problems(problems)
        first = self.problems[0].problem if self.problems else "unknown"
        super().__init__(first, source=source, hint=hint, exit_code=exit_code)

    def render(self) -> str:

        return render_problems(
            self.kind,
            self.problems,
            source=self.source,
            hint=self.hint or "Fix the values above, then run `mockrelay validate`.",
        )


class ConfigLoadError(ConfigError):
    kind = "Configuration error"
    code = "config_load"


class FixtureError(MockRelayError):
    kind = "Fixture error"
    code = "fixture"


class FixtureSchemaError(FixtureError):
    kind = "Invalid fixture"
    code = "fixture_schema"

    def __init__(
        self, problems: Iterable[Problem], source: str = "", hint: str = ""
    ) -> None:
        self.problems = as_problems(problems)
        first = self.problems[0].problem if self.problems else "unknown"
        super().__init__(first, source=source, hint=hint)

    def render(self) -> str:
        return render_problems(
            self.kind, self.problems, source=self.source, hint=self.hint
        )


class StoreError(FixtureError):
    kind = "Fixture store error"
    code = "store"


class SecurityError(MockRelayError):
    kind = "Refused for security reasons"
    code = "security"


class FramingError(SecurityError):
    """The request says something incoherent about where its body ends.

    Distinct from a plain SecurityError because it is the one refusal the
    server cannot recover a connection from: the body was never read, so
    those bytes are still in the socket and the next keep-alive read would
    start in the middle of them. The connection has to be closed.
    """

    kind = "Malformed request"
    code = "malformed_request"


class UpstreamError(MockRelayError):
    kind = "Upstream request failed"
    code = "upstream"


class LimitExceeded(MockRelayError):
    kind = "Limit exceeded"
    code = "limit"
    status = 413

    def __init__(
        self, message: str, status: int = 413, hint: str = "", source: str = ""
    ) -> None:
        super().__init__(message, source=source, hint=hint)
        self.status = status


class ValidationFailed(MockRelayError):
    exit_code = EXIT_VALIDATION
    kind = "Validation failed"
    code = "validation"

    def __init__(
        self, problems: Iterable[Problem], source: str = "", hint: str = ""
    ) -> None:
        self.problems = as_problems(problems)
        super().__init__(
            self.problems[0].problem if self.problems else "", source=source, hint=hint
        )

    def render(self) -> str:
        return render_problems(
            self.kind, self.problems, source=self.source, hint=self.hint
        )


class DoctorFailed(MockRelayError):
    exit_code = EXIT_DOCTOR
    kind = "Environment check failed"
    code = "doctor"

    def __init__(
        self, problems: Iterable[Problem], source: str = "", hint: str = ""
    ) -> None:
        self.problems = as_problems(problems)
        super().__init__(
            self.problems[0].problem if self.problems else "", source=source, hint=hint
        )

    def render(self) -> str:
        return render_problems(
            self.kind, self.problems, source=self.source, hint=self.hint
        )
