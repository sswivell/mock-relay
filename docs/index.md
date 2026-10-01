# MockRelay

Record real HTTP traffic once. Replay it offline, as often as you like.

MockRelay is a local HTTP proxy. In **record** mode it forwards your requests to
the real service and saves each exchange as a JSON fixture. In **replay** mode
it answers entirely from those files, with no outbound network calls at all.

It is built for **HTTP mocking**, **API recording**, **API replay**, and
**deterministic API testing**: local development against a real API shape,
integration tests that do not depend on a third party's uptime, and CI that does
not burn someone else's rate limit.

## Install

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Requires Python 3.10 or newer. The only runtime dependency is PyYAML.

Or run it in a container, with no Python on the host:

```bash
docker build -t mockrelay https://github.com/sswivell/mock-relay.git
docker run --rm -v "$PWD:/work" -p 8080:8080 -p 8081:8081 mockrelay serve --mode replay
```

!!! info "Not on PyPI yet"
    MockRelay is not published to PyPI, so the install command above names git
    explicitly. It builds the same tagged source as the release workflow. Once a
    release ships, `pip install mockrelay` will work unchanged.

## Quick start

```bash
mockrelay init                          # write a starter mockrelay.yaml
mockrelay serve --mode record           # proxy and record

# in another terminal
curl http://localhost:8080/gh/users/octocat

mockrelay list                          # see what was recorded
mockrelay serve --mode replay           # replay it, offline
```

The first path segment picks the upstream, so `/gh/users/octocat` is forwarded to
the `gh` entry in your config. `mockrelay init` writes one:

```yaml
listen: '127.0.0.1:8080'
admin_listen: '127.0.0.1:8081'
fixtures_dir: './fixtures'
mode: record
latency_ms: 0
redact_headers: [authorization, cookie, x-api-key]
normalize_json_paths: ['$.id', '$.created']
match_mode: auto
fuzzy_threshold: 0.86
ignore_case: false
match_priority: [path, body, query, literal]
smart_record_paths: true
upstreams:
  gh:
    base_url: 'https://api.github.com'
    mode: record
```

Run the same curl again in replay mode and you get the recorded response back:

```http
HTTP/1.1 200 OK
X-MockRelay-Match: exact
X-MockRelay-Fixture: gh-get-016c60e26e39
X-MockRelay-Score: 4000009
```

Pull the plug on the network and it still works. That is the whole idea.

## Why bother

- **Repeatable.** The same fixture returns the same bytes every run, so a test
  that passed yesterday passes today. An upstream outage cannot turn your build
  red.
- **Cheap.** You stop spending a third party's rate limit on your own CI.
- **Offline.** Your whole external API surface runs on `127.0.0.1`. Work on a
  train, on a plane, behind an outage.
- **Safe to commit.** Secrets are redacted to `{{SECRET}}` and volatile IDs
  become `{{NORMALIZED}}` before anything is written to disk, so fixtures are
  plain JSON you can read, diff, and check in.

## When MockRelay is the wrong tool

There are several good reasons not to reach for this:

| If you need to… | Use instead |
|---|---|
| Invent responses that never happened | WireMock, Prism, or hand-written route handlers |
| Generate different behaviour per test run | A programmatic stub in your test code |
| Mock inside one process, with no server | `responses`, `respx`, or `vcrpy` |
| Record and edit a HAR from a browser | mitmproxy, or the devtools network panel |
| Intercept arbitrary protocols | A general-purpose proxy such as mitmproxy or Envoy |

MockRelay replays traffic that was really recorded. If the response you need was
never observed, it is the wrong shape of tool.

## What you get

- **Four modes** - `record`, `replay`, `passthrough`, `hybrid`. Set them
  globally, per upstream, or per route prefix.
- **Ranked matching** - `exact`, `wildcard`, `regex`, and `fuzzy` paths are
  scored and sorted, so the most specific fixture wins instead of whichever file
  the filesystem listed first.
- **Query and body matching** - a fixture can pin the query parameters it cares
  about, and match on the body with `body_contains` and operators like `$gt`,
  `$in`, and `$regex`.
- **Redaction and normalization** - header and body secrets are masked; volatile
  fields are replaced so re-recording diffs cleanly.
- **Latency and fault injection** - add delay, or fail a fraction of requests
  with a `429`, to exercise your retry and backoff.
- **A CLI** - `serve`, `record`, `replay`, `list`, `match`, `validate`, `stats`,
  `clean`, `init`, `config`. Most take `--json`.
- **An admin UI and API** on `:8081`, with a dashboard, `/api/match`, and
  Prometheus `/metrics`.

## How ranking works

A fixture describes what it should answer: the method, the path, the query
parameters it constrains, and the body fields it constrains. MockRelay scores
every candidate and serves the most specific one.

Here is real `mockrelay match` output for `GET /orders/101` against a `shop`
upstream that has six fixtures:

```text
  hit  prio  strategy  score    status  id                    path
  ────────────────────────────────────────────────────────────────────────
  yes  0     exact     4000009  200     shop-exact-order-101  /orders/101 [exact] vs /orders/101
  yes  0     wildcard  3000008  200     shop-wildcard-orders  wildcard:/orders/* [wildcard] vs /orders/101
  yes  0     regex     2000009  200     shop-regex-orders     re:^/orders/\d+$ [regex] vs /orders/101
  yes  0     fuzzy     1000009  200     shop-fuzzy-orders     fuzzy:/ordres/101 [fuzzy] vs /orders/101
  no   0     miss      0        200     shop-glob-files       wildcard:/files/** [wildcard] vs /orders/101
  no   0     miss      0        201     shop-post-order       /orders [exact] vs /orders/101
```

Specificity bands, highest first:

| Strategy | Prefix in the fixture | Band |
|---|---|---|
| exact | the path itself, or `exact:` | 4 |
| wildcard | `wildcard:`, `glob:` | 3 |
| regex | `re:`, `regex:` | 2 |
| fuzzy | `fuzzy:` | 1 |
| priority | an integer `priority` on the fixture | outranks them all |

`match_priority` reorders what counts as more specific - put `query` first when
a query parameter identifies the resource better than the path does. It changes
the `rank` tuple, not the flat `score`, so compare `rank` when you want to know
why one fixture won.

## A recorded fixture

Plain JSON, on disk, under `fixtures/<upstream>/`. Easy to read, easy to diff,
easy to hand-edit:

```json
{
  "id": "gh-get-016c60e26e39",
  "upstream": "gh",
  "match": {
    "method": "GET",
    "path": "/users/octocat",
    "query_subset": {}
  },
  "request": {
    "method": "GET",
    "path": "/users/octocat",
    "query": {},
    "headers": { "Authorization": "{{SECRET}}" },
    "body": null
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "body": {
      "login": "octocat",
      "id": "{{NORMALIZED}}",
      "type": "User",
      "created": "{{NORMALIZED}}",
      "request_id": "req_live_9f2a"
    }
  },
  "normalize": ["$.id", "$.created"],
  "recorded_at": "2026-09-30T01:23:39Z",
  "call_index": 0
}
```

Point an existing client at the proxy and nothing else changes:

```python
import httpx

client = httpx.Client(base_url="http://localhost:8080/gh")

response = client.get("/users/octocat")
response.status_code                    # 200
response.headers["X-MockRelay-Match"]    # "exact"
response.headers["X-MockRelay-Fixture"]  # "gh-get-016c60e26e39"
```

## When a request matches nothing

Replay mode answers `501` and tells you what it had, so you can see how close you
were:

```json
{
  "error": "no fixture matched",
  "method": "GET",
  "path": "/users/definitely-not-recorded",
  "match_mode": "auto",
  "nearest": ["gh-get-016c60e26e39"]
}
```

## Checking the fixtures in CI

`mockrelay validate` loads the config and every fixture without starting a
server. It exits `4` if anything is wrong, so a pipeline can gate on it:

```bash
mockrelay validate || exit 1
```

## Where to go next

- [Getting started](getting-started.md) - the full walkthrough
- [Operating modes](modes.md) - what record, replay, passthrough, and hybrid do
- [Smart matching](matching.md) - strategies, operators, and debugging a miss
- [Fixtures and redaction](fixtures.md) - the schema and secret masking
- [Common recipes](recipes.md) - SDK redirection, retry testing, CI gating
- [Comparisons](comparisons.md) - where this fits against vcrpy, WireMock, mitmproxy, and the rest
- [CLI reference](cli.md) - every command and flag
- [Configuration](configuration.md) - every key, with defaults
- [Admin API and UI](admin.md) - the dashboard and JSON endpoints
- [Architecture](architecture.md) - how a request flows through the code
- [Development](development.md) - local setup, tests, and linting

## Project

MockRelay is MIT licensed and developed at
[github.com/sswivell/mock-relay](https://github.com/sswivell/mock-relay).
