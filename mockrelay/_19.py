"""Machine-readable output for the CLI.

A script that wants to know what is recorded should not have to parse
box-drawing characters, so every read-only command can describe its result
as data instead. One envelope covers all of them: the command name, whether
it succeeded, and either ``data`` or ``problems``. The schema field exists
so a future change of shape can be detected rather than guessed at.
"""

from __future__ import annotations

import json

from .errors import Problem, as_problems

SCHEMA = 1


def _01(
    command: str, data: object = None, problems=None, extra: dict | None = None
) -> None:
    """Print one result envelope as JSON on stdout."""
    out: dict = {"schema": SCHEMA, "command": command, "ok": not problems}
    if problems:
        out["problems"] = [_02(p) for p in as_problems(problems)]
    if data is not None:
        out["data"] = data
    if extra:
        out.update(extra)
    print(json.dumps(out, indent=2, default=str))


def _02(problem) -> dict:
    if isinstance(problem, Problem):
        return problem.as_dict()
    return {"problem": str(problem)}
