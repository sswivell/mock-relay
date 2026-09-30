# MockRelay Launch Material

Draft announcements and community posts. No fluff, no fabricated metrics, no begging for stars. Just a developer explaining what problem MockRelay solves, how it works, and what makes it interesting.

## Before you post

Two things to get right, because a broken install command is the first thing a
reader tries.

**1. Install.** MockRelay is not on PyPI. The command that works today is:

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Once a PyPI release exists, `pip install mockrelay` is the shorter form and every
draft below reads better with it. Do not claim a PyPI release that does not
exist yet.

**2. Links.** Both of these are live and can be used as-is:

- Site: <https://sswivell.github.io/mock-relay/>
- Release: <https://github.com/sswivell/mock-relay/releases/tag/v1.0.0>

### What is safe to claim, and what is not

Safe, because the test suite and `examples/matching_demo.py` demonstrate it:
the record/replay behaviour, the ranking order, the redaction, the body
operators, `match_priority`, and the CLI surface.

Not safe: adoption, stars, downloads, user counts, or any comparison to another
project. Do not add them, and do not add a "stars welcome" line. If a number
would be flattering but unverifiable, leave it out.

---

## 1. Hacker News (Show HN)

**Title:** Show HN: MockRelay – Record real HTTP traffic once, replay it locally and offline

**Post Body:**

Hey HN,

I got tired of depending on live third-party APIs during local development and CI runs. Sandbox environments go down, test credentials expire, rate limits kick in, and hitting real endpoints slows down test suites.

I built MockRelay (https://github.com/sswivell/mock-relay) to solve this without writing bespoke mocks for every service.

**How it works:**
MockRelay acts as a lightweight local proxy. In `record` mode, you point your app at `http://localhost:8080/<upstream-name>/...`. It forwards requests to the real upstream (e.g., Stripe or GitHub) and saves each request and response as a clean JSON fixture on disk. In `replay` mode, it serves those fixtures locally with zero outbound network calls.

**What makes it interesting:**
Most mock tools use naive "first fixture that matches" logic. If you have a glob like `/users/*` and an exact match `/users/42`, whichever file loaded first wins.

MockRelay ranks candidates deterministically instead:
- Specificity bands: `exact` > `wildcard` > `regex` > `fuzzy`.
- Partial JSON body matching with comparison operators (`$gt`, `$in`, `$regex`, JSONPath keys like `$.items[*].sku`).
- Query-subset matching (`?page=2&sort=asc`).
- Reversible `match_priority`: if query parameters matter more than the path for a particular route, configure `match_priority: [query, path, body, literal]`.
- Built-in CLI preview: `mockrelay match /orders/42 -m POST -b '{"total": 500}'` shows how a request scores against stored fixtures without starting a server. `examples/matching_demo.py` runs this and prints the ranking.
- Automatic secret redaction: Authorization headers, API keys, and sensitive tokens become `{{SECRET}}` before anything touches disk, on both the request and response side.

It also has `mockrelay validate`, which checks a config and its fixtures without
starting a server or touching the network, and exits `4` on a problem so a CI
step can gate on it.

Python 3.10+, one runtime dependency (PyYAML), MIT licensed.

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Source: https://github.com/sswivell/mock-relay
Docs: https://sswivell.github.io/mock-relay/
Release: https://github.com/sswivell/mock-relay/releases/tag/v1.0.0

I would like to hear which of these you would use, and which parts of the
problem it does not solve.

---

## 2. Reddit (r/Python, r/webdev, r/programming)

**Title:** I built MockRelay: a local HTTP proxy to record real API traffic and replay it deterministically

**Post Body:**

Like many developers, I spent too much time dealing with broken local environments because a third-party sandbox API was having an outage or rate-limiting my team.

I built **MockRelay**, an open-source HTTP proxy and mock server:
https://github.com/sswivell/mock-relay

The workflow is simple:
1. `mockrelay serve --mode record`
2. Point your app at `http://localhost:8080/<upstream>/<path>` instead of the live URL.
3. Your app makes normal requests; MockRelay forwards them upstream and stores clean, redacted JSON fixtures in `./fixtures/<upstream>/`.
4. Switch to `mockrelay serve --mode replay` and run your app or test suite completely offline.

A few things that made building this interesting:
- **Ranked matching:** Instead of returning the first matching fixture, MockRelay scores candidates by specificity (`exact` > `wildcard` > `regex` > `fuzzy`), body constraint count, and literal character density. An exact match `/users/42` always outranks a wildcard `/users/*`, regardless of file order on disk.
- **Deep body matching:** You can match JSON bodies using MongoDB-style operators (`$gt`, `$lte`, `$regex`, `$in`) and JSONPath keys.
- **Configurable priority:** You can reorder ranking criteria using `match_priority` (globally, per upstream, or per route) or assign an explicit integer priority to a fixture.
- **Sanitization:** Request/response headers and bodies pass through a redaction pipeline so secrets don't accidentally get checked into git.
- **CLI diagnostics:** `mockrelay match <path>` gives you a diagnostic breakdown of every candidate fixture and why it won or failed.

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Python 3.10+, PyYAML as the only runtime dependency.

There is a worked demo script if you want to see the whole record/replay switch
without setting anything up: https://sswivell.github.io/mock-relay/demo/

I am curious how people here currently handle third-party API mocking, and
whether this fits the shape of your workflow.

---

## 3. GitHub Discussion / Release Announcement

**Title:** MockRelay 1.0: Record real HTTP traffic once, replay it locally and deterministically

**Body:**

MockRelay 1.0 is now available!

MockRelay is a local HTTP proxy designed to eliminate flaky third-party API dependencies during local development and automated testing.

### Highlights:
- **Record & Replay Modes:** Capture real HTTP requests and responses as plain JSON files, then replay them offline with optional latency simulation or error injection.
- **Ranked Smart Matching:** Candidate fixtures are scored and ranked so the most specific fixture wins (`exact` > `wildcard` > `regex` > `fuzzy`). Supports deep JSON body operators (`$gt`, `$regex`, JSONPath) and query-subset matching.
- **Configurable Priority:** Use `match_priority` to prioritize query or body matching over path matching when needed.
- **Automatic Redaction:** Sensitive headers (API keys, bearer tokens) and credentials in payloads are automatically masked to `{{SECRET}}`.
- **Validation & CLI Tooling:** Includes `mockrelay validate` to verify config and fixture integrity in CI, `mockrelay match` to test matching rules offline, and `mockrelay stats` / `clean` for fixture management.

### Getting started

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
mockrelay init
mockrelay serve --mode record     # records into ./fixtures/
mockrelay serve --mode replay      # replays from disk, no network
```

Release: https://github.com/sswivell/mock-relay/releases/tag/v1.0.0
Documentation: https://sswivell.github.io/mock-relay/
Issues and contributions: https://github.com/sswivell/mock-relay/issues

Not on PyPI yet, which is why the install command names git explicitly.

---

## 4. General Developer Community (Discord, Slack, Mastodon, X)

Local dev kept breaking whenever a third-party sandbox API went down or rate
limited us, so I built **MockRelay** — a local HTTP proxy that records real API
traffic as plain JSON fixtures and replays them offline, deterministically.

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

The part I found most interesting to build: most mock tools return the first
fixture that matches, so a broad `/users/*` can shadow an exact `/users/42`
depending on file order. MockRelay ranks candidates by specificity instead, so
the specific one wins regardless of what is on disk.

- JSON body operators (`$gt`, `$in`, `$regex`, JSONPath) and query-subset matching
- `match_priority` to reorder ranking when query params identify a resource better than the path
- Secrets redacted to `{{SECRET}}` before anything is written, request and response both
- Latency simulation and error injection for retry testing

MIT, Python 3.10+, PyYAML as the only runtime dependency.
https://github.com/sswivell/mock-relay
