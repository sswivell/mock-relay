# Reddit drafts

One draft per subreddit. Do not cross-post the same text. Do not paste any of
these verbatim: write them in your own voice, which is both what the
communities expect and what makes them worth reading.

Reddit's rules pages now return 403 to automated requests and
`old.reddit.com` redirects to login, so everything below came from mirrors and
is dated. Re-check each `/about/rules` page in a logged-in browser before
posting.

---

## r/SideProject

URL: https://www.reddit.com/r/SideProject/
Rules verified: 2026-09-26. No subreddit-specific rules published. Say plainly
it is yours, use the right flair, make the post useful on its own.
Status: ready once rewritten.

**Title**

```text
I built a local HTTP proxy that records real API traffic and replays it offline
```

**Body**

```text
Disclosure: I wrote this, it is mine, MIT licensed.

The problem I kept hitting was that our test suite kept going red for reasons
that had nothing to do with our code. A third-party sandbox would rate-limit
us, or go down, or take forty seconds, and we would spend an afternoon
bisecting a bug that was actually somebody else's outage.

So I built MockRelay: https://github.com/sswivell/mock-relay

It is a local HTTP proxy. You point your app at
http://localhost:8080/<upstream>/<path> instead of the real URL:

  mockrelay serve --mode record
  # drive your app normally, every request gets written to
  # fixtures/<upstream>/*.json with secrets redacted
  mockrelay serve --mode replay
  # same requests, served from those files, no network at all

The fixtures are plain JSON, so they diff cleanly and can sit in the repo next
to the tests.

The part I found most interesting was fixture selection. Most mock tools return
the first fixture that matches, which means a broad /users/* can shadow an
exact /users/42 depending on what order the filesystem gave you. MockRelay
scores every candidate instead, so the specific one always wins:

  exact > wildcard > regex > fuzzy, then by body and query
  constraint count, then by literal density.

Bodies can match with operators instead of exact equality, which is what made
the ranking actually earn its keep:

  body_contains:
    total: { "$gt": 100 }
    $.items[*].sku: "wildcard:A*"

Python 3.10+, PyYAML is the only runtime dependency. Not on PyPI yet, so:

  pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

Interested in how people here handle third-party APIs in tests. VCR at the
client layer, a hand-written mock server, a shared sandbox, or something I have
not thought of.
```

---

## r/opensource

URL: https://www.reddit.com/r/opensource/
Rules verified: 2026-09-26. Keep self-promotion under 10% of your posts. Flair
`Promotional` is required. Repo must have an OSI-approved LICENSE, or the post
is removed. No link aggregations.
Status: ready once rewritten.

Note the LICENSE rule: MockRelay has MIT at the repo root, so this is satisfied.

**Title**

```text
MockRelay: an open source HTTP record/replay proxy with ranked fixture matching
```

**Body**

```text
Disclosure: this is my project. MIT licensed, Python 3.10+, one runtime
dependency (PyYAML).

https://github.com/sswivell/mock-relay

MockRelay is a local HTTP proxy for recording real API traffic and replaying it
from deterministic JSON fixtures. It exists because writing and maintaining
hand-written mock servers does not scale, and depending on a live third-party
API in tests makes your suite slow and someone else's uptime your problem.

Record mode forwards to the real service and writes each exchange to
fixtures/<upstream>/*.json. Replay mode serves those files and makes no
outbound calls. Request and response headers and bodies both go through
redaction, so tokens come out as {{SECRET}} before anything is written.

The part that differs from the usual first-match-wins approach is ranked
matching. Candidates are scored by path specificity (exact > wildcard > regex >
fuzzy), then body and query constraint count, then literal density, so
/users/42 beats /users/* regardless of file order. There is also a CLI,
`mockrelay match`, that prints the ranking and the per-check reason for every
candidate without starting a server.

It is early: v1.0.0, one release, no PyPI yet. Happy to answer questions, and
especially interested in hearing where this is the wrong tool.
```

---

## r/webdev — Showoff Saturday

URL: https://www.reddit.com/r/webdev/
Rules verified: 2026-09-26. Project showoffs are **limited to Showoff
Saturday**; any other day the post is removed. Correct flair enforced. "Think
project, not product. Focus on the technical details." LLM-generated
low-effort posts are removed.
Status: drafted. Post on a Saturday.

**Title**

```text
Show r/webdev: I built an HTTP proxy that records real API traffic and replays it offline, ranked fixture matching
```

**Body**

```text
Disclosure: my project. MIT, Python.

https://github.com/sswivell/mock-relay

I got tired of frontend work stopping because a backend or a third-party API
was not available locally, so I built a proxy that records real API traffic
once and replays it as JSON fixtures.

The interesting technical part was fixture selection, because the naive version
of this is a bug waiting to happen. Most record/replay tools return the first
fixture that matches, so a recorded wildcard:/users/* shadows a recorded
/users/42 depending on directory iteration order. That reproduces on your
machine and not in CI, for no reason connected to your change.

MockRelay scores candidates instead. Path strategy sets a specificity band
(exact 4, wildcard 3, regex 2, fuzzy 1), then body and query constraint count,
then literal density. So the ranking is a tuple and file order is not part of
the key. You can reorder the whole thing with match_priority when a query
param identifies a resource better than the path does.

Second thing I got wrong initially: I only redacted the request side. Tokens
come back in response bodies constantly, so fixtures are built from the
redacted body on both sides now, and the match spec is derived from the
redacted body too, so a secret cannot leak through a body constraint.

Four modes (record, replay, passthrough, hybrid), set globally, per upstream,
or per route. CI recipe is just `mockrelay validate` (exits 4 on a broken
fixture) then start it in replay mode.

Python 3.10+, PyYAML only, not on PyPI yet:

  pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

Would love to hear how people here mock backends for frontend work, and where
this overlaps with what you already use.
```

---

## r/Python — monthly showcase thread only

URL: https://www.reddit.com/r/Python/
Rules verified: 2026-09-26. **Standalone showcase posts are no longer allowed.**
They go in the monthly showcase post or a daily thread. Must be a text post,
must have showcase flair, must link to source, and must contain the sections
below. Re-check this rule: it changed during 2026.
Status: ready once rewritten. Post as a comment in the monthly showcase thread,
not as a new submission.

The three required sections are **What My Project Does**, **Target Audience**,
and **Comparison**. This is drafted to match them exactly.

```text
**MockRelay** — MIT, Python 3.10+, one runtime dependency (PyYAML)
Source: https://github.com/sswivell/mock-relay

**What My Project Does**

MockRelay is a local HTTP proxy that records real API traffic and replays it
from JSON fixtures. You point your app at
http://localhost:8080/<upstream>/<path> instead of the real URL. In record
mode it forwards upstream and writes each exchange to
fixtures/<upstream>/*.json with secrets redacted. In replay mode it serves
those files and makes no network calls at all, so tests and local dev work
offline.

Fixtures are matched by rank, not by file order: path specificity
(exact > wildcard > regex > fuzzy), then body and query constraint count, then
literal density. Bodies match with operators ($gt, $in, $regex, and others)
over JSONPath-style keys, so a fixture can assert "total > 100" rather than one
exact value.

```python
import httpx

client = httpx.Client(base_url="http://localhost:8080/gh")
resp = client.get("/users/octocat")
```

**Target Audience**

Anyone whose tests or local development depend on an HTTP API they do not
control: third-party services, another team's backend, or their own service
before it is deployed. Useful for deterministic integration tests, for CI
without burning someone else's rate limit, and for reproducing a specific
error response.

**Comparison**

vcrpy and responses/respx operate inside a single test process and patch the
HTTP client; MockRelay runs as a separate local proxy, so anything that speaks
HTTP can use it, including apps you did not write in Python. WireMock and Prism
generate responses from a hand-written spec; MockRelay's source of truth is
recorded real traffic. mitmproxy is for inspecting traffic; MockRelay is for
replaying it. If you need to invent responses that never happened, WireMock is
the better fit — this only helps when you have real traffic to capture.

Not on PyPI yet, so the install is:

    pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

Looking for feedback on the ranking design and on what I have got wrong.
```

---

## r/devops — weekly self-promotion thread

URL: https://www/devops/
Rules verified: 2026-09-26. Self-promotion goes **in the weekly self-promotion
thread** and nowhere else. Affiliation must be disclosed at the top. Not just a
link — there has to be discussion. No blog links.
Status: drafted. Write this as a comment in the next weekly thread.

```text
Full disclosure up front: I maintain this.

I keep seeing CI jobs that call third-party APIs during integration tests. It
is slow, it is flaky in a way that has nothing to do with your code, and it
spends somebody else's rate limit on every run. MockRelay
(https://github.com/sswivell/mock-relay, MIT) is a local HTTP proxy that
records real API traffic once and replays it from JSON fixtures.

The pipeline shape is short:

    - run: mockrelay validate          # exits 4 on a bad config or fixture
    - run: mockrelay replay --latency 0 &
    - run: pytest tests/integration -q

No network, no credentials, no sandbox. `validate` is the part worth stealing
even if you use something else: it loads every fixture without starting a
server and fails the job with the file and the reason, so a hand-edited
fixture does not turn into an unexplained 501 mid-suite.

It also injects latency and error rates per route, which is how I test retry
and backoff without waiting for a real 429.

Python 3.10+, PyYAML only, not on PyPI yet.

I am mostly unsure about container ergonomics and about whether anyone runs
this in a job matrix. If you have done either, I would like to hear how.
```

---

## Not doing

| Subreddit | Why |
|---|---|
| r/programming | Rule: "not the place to post a project to get feedback, ask for help, or otherwise promote it." A technical write-up is allowed but a project link is not. Also has an explicit no-LLM-content rule. |
| r/softwaretesting | Commercial and self-promotional testing-tool links are removed, and a karma gate for low-account-age was added in July 2026. |
| r/ExperiencedDevs | "No Surveys/Advertisements" plus a 3+ years experience gate. |
| r/TestAutomation | Dormant. Indexed posts stop in 2020. |