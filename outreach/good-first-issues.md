# Good first issues

The repo had a `good first issue` label, a CONTRIBUTING.md section pointing at
it, and nothing behind it. A prospective contributor who clicks that link and
finds an empty list concludes the project has no room for them.

These three are scoped to be finishable in a single sitting, they are
independent of each other, and they are real gaps rather than busywork.

Status: **submitted**.

---

## Issue 1 — good first issue, documentation

**Title**

```text
Add a recipe for running the integration suite against MockRelay in GitHub Actions
```

**Labels:** `good first issue`, `documentation`

**Body**

```markdown
`docs/recipes.md` has a CI section, but it is two lines of bash:

    mockrelay validate || exit 1

That tells you the fixtures are valid. It does not show the thing people
actually need, which is starting the proxy in replay mode, waiting for it to
be listening, running the suite against it, and tearing it down afterwards so
the job does not hang.

Please add a complete GitHub Actions workflow example. The requirements:

- `pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"`
- a `validate` step that fails the job on a broken config or fixture
- starting `mockrelay replay` in the background
- a real readiness wait, not a fixed `sleep`, so the job is not flaky
- running `pytest` against it
- teardown, so the workflow does not hang on the background process

`examples/ci_replay.py` is a working smoke test you can point the workflow at.
If you can find how to wait on the admin port (`8081` by default) rather than
sleeping, that would be better than a fixed delay, and worth a note in the
docs about why.

Add it to the end of `docs/recipes.md`. No code changes needed.

Claim this issue before you start so nobody duplicates the work.
```

---

## Issue 2 — good first issue, tests

**Title**

```text
Test coverage for redaction of nested and array-shaped secrets
```

**Labels:** `good first issue`, `tests`

**Body**

```markdown
`tests/test_redact.py` and `tests/test_record_redaction.py` cover header
redaction and flat string values in a JSON body. What I am not sure is covered
is a secret that is not at the top level of the body.

Cases I would like covered:

- a token nested several objects deep, `{"data": {"session": {"token": "..."}}}`
- a token inside an array of objects, `{"items": [{"token": "..."}]}`
- a value that *looks* like a credential but is not, so redaction does not eat
  legitimate data. An opaque-looking identifier with no matching prefix is the
  interesting one.
- redaction being idempotent: redacting an already-redacted payload does not
  turn `{{SECRET}}` into something else

The behaviour is in `mockrelay/_07.py`. `tests/test_redact.py` has the existing
style to follow.

If you find a case the current implementation gets wrong, that is even better
than a test that passes, and there is a `bug` label for it. Either way, please
say which it turned out to be.

Claim this issue before you start so nobody duplicates the work.
```

---

## Issue 3 — good first issue, documentation

**Title**

```text
Document the fixture schema from an actual fixture, not a hand-written example
```

**Labels:** `good first issue`, `documentation`

**Body**

```markdown
`docs/fixtures.md` documents the schema, and `docs/index.md` shows a fixture
that is mostly plausible but has been edited down for readability. A reader has
no way to tell which fields are always present, which are optional, and which
only appear when the recorder wrote them.

Please regenerate the example in `docs/fixtures.md` from a real recording.
`examples/matching_demo.py` builds fixtures in a temp directory and you can
read them straight off disk, which avoids needing to hit the network.

For each field, mark it as required, optional, or "present only when the
recorder wrote it". Cover at least:

- `match.query_subset` when the request had no query parameters
- `normalize`, and what happens when it is empty
- `call_index`, and whether it matters for replay
- `recorded_at`

Keep the current style: prose for the required-versus-optional distinction, JSON
for the examples. `python scripts/check_docs_nav.py` has to pass before you push.

Claim this issue before you start so nobody duplicates the work.
```