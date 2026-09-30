# MockRelay Launch Material

Draft announcements and community posts. No fluff, no fabricated metrics, no begging for stars. Just a developer explaining what problem MockRelay solves, how it works, and what makes it interesting.

**Before posting:** substitute the install command with the one that is true at
the time of posting. MockRelay is not on PyPI yet, so the working command today
is:

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Once a PyPI release exists, `pip install mockrelay` is the shorter form and the
drafts below read better with it. Do not claim a PyPI release that does not
exist.

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

MockRelay implements deterministic, ranked matching:
- Specificity bands: `exact` > `wildcard` > `regex` > `fuzzy`.
- Partial JSON body matching with comparison operators (`$gt`, `$in`, `$regex`, JSONPath keys like `$.items[*].sku`).
- Query-subset matching (`?page=2&sort=asc`).
- Reversible `match_priority`: if query parameters matter more than the path for a particular route, you can configure `match_priority: [query, path, body, literal]`.
- Built-in CLI preview: `mockrelay match /orders/42 -m POST -b '{"total": 500}'` lets you inspect how requests score and rank against stored fixtures without starting a server.
- Automatic secret redaction: Authorization headers, API keys, and sensitive tokens are converted to `{{SECRET}}` before anything touches disk.

It's written in Python (3.10+), packaged with zero runtime dependencies beyond PyYAML, and ships under an MIT license.

Source: https://github.com/sswivell/mock-relay
Docs: https://sswivell.github.io/mock-relay/

Feedback, bug reports, and PRs are very welcome.

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

It requires Python 3.10+ and only PyYAML as an external runtime dependency.

Would love to hear how you currently handle third-party API mocking in your projects and if this fits your workflow.

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

### Getting started:
```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
mockrelay init
mockrelay serve --mode record
```

Documentation: https://sswivell.github.io/mock-relay/
Issues & Contributions: https://github.com/sswivell/mock-relay/issues

---

## 4. General Developer Community (Discord, Slack, Mastodon, X)

I got tired of broken dev environments whenever third-party sandbox APIs went down or hit rate limits, so I built **MockRelay**:
https://github.com/sswivell/mock-relay

It's a local HTTP proxy that records live API traffic as plain JSON fixtures and replays them offline deterministically.

Notable features:
- Ranked fixture matching (most specific fixture wins; no naive first-match surprises)
- JSON body operator matching (`$gt`, `$in`, `$regex`, JSONPath)
- Query-subset matching & customizable `match_priority`
- Automatic secret redaction for safe version control
- Latency simulation & error injection for retry testing

Free, open source (MIT), Python 3.10+, zero heavy dependencies.
