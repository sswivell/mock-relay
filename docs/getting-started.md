# Getting started

Install MockRelay, write a config, and run your first record and replay cycle.
It takes about five minutes and needs no credentials to get to the end of it.

Every command and output on this page is copied from a real run.

---

## 1. Installation

MockRelay requires Python 3.10 or later. The supported install pulls the tagged
source straight from GitHub, so there is nothing to trust but this repository:

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

!!! info "Not on PyPI yet"
    MockRelay has not been published to PyPI. Until it is, the command above is
    the supported install and builds the same sources as the release workflow.
    When a release ships, `pip install mockrelay` will work unchanged.

### From source

For local development or contributing:

```bash
git clone https://github.com/sswivell/mock-relay.git
cd mock-relay
pip install -e ".[dev]"
```

Verify your installation:

```bash
mockrelay --version
```

```text
mockrelay 1.0.0
```

---

## 2. Initialize the configuration

Run `mockrelay init` in your project root to generate a starter `mockrelay.yaml`:

```bash
mockrelay init
```

This writes exactly this, and nothing else:

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

Add an upstream per service you want to record. The first path segment of a
request picks which one:

```yaml
upstreams:
  gh:
    base_url: 'https://api.github.com'
  stripe:
    base_url: 'https://api.stripe.com'
```

`init` refuses to overwrite an existing file. Pass `--force` to replace one, or
give it a path: `mockrelay init config/mockrelay.yaml`.

Every key above is covered in [Configuration](configuration.md).

---

## 3. How proxy routing works

The first path segment names the upstream; everything after it is the path that
gets forwarded:

```text
http://127.0.0.1:8080/<upstream-key>/<endpoint-path>
```

| Request URL | Upstream | Forwarded to |
|---|---|---|
| `http://localhost:8080/gh/users/octocat` | `gh` | `https://api.github.com/users/octocat` |
| `http://localhost:8080/stripe/v1/charges` | `stripe` | `https://api.stripe.com/v1/charges` |

Fixtures are stored per upstream, under `fixtures/<upstream-key>/`, so the
segment you choose becomes the directory name in your repository.

A request whose first segment does not name a configured upstream is refused
rather than guessed at:

```json
{ "error": "unknown upstream 'gh'" }
```

---

## 4. Record your first fixture

1. Start MockRelay in record mode:

   ```bash
   mockrelay serve --mode record
   ```

   *(You can also use the shorthand command `mockrelay record`.)*

2. Send a request to the proxy:

   ```bash
   curl -i http://localhost:8080/gh/users/octocat
   ```

3. MockRelay proxies the request to GitHub, returns the live response to your
   client, and writes a fixture to `./fixtures/gh/`. The response carries one
   extra header:

   ```http
   X-MockRelay-Match: record
   ```

4. Check your recorded fixtures:

   ```bash
   mockrelay list
   ```

   ```text
     upstream  method  path                status  id
     ─────────────────────────────────────────────────
     gh        GET     /users/octocat      200     gh-get-016c60e26e39
   ```

5. Read the fixture. It is plain JSON, and anything sensitive has already been
   replaced — `Authorization: {{SECRET}}`, `"id": "{{NORMALIZED}}"`:

   ```json
   {
     "id": "gh-get-016c60e26e39",
     "upstream": "gh",
     "match": { "method": "GET", "path": "/users/octocat", "query_subset": {} },
     "request": {
       "method": "GET",
       "path": "/users/octocat",
       "headers": { "Authorization": "{{SECRET}}" },
       "body": null
     },
     "response": {
       "status": 200,
       "headers": { "Content-Type": "application/json" },
       "body": { "login": "octocat", "id": "{{NORMALIZED}}" }
     },
     "normalize": ["$.id", "$.created"],
     "recorded_at": "2026-09-30T01:44:41Z"
   }
   ```

   The ID is derived from the upstream, method, and path, so re-recording the
   same request overwrites the same file instead of piling up duplicates.

---

## 5. Replay it offline

1. Start MockRelay in replay mode:

   ```bash
   mockrelay serve --mode replay --latency 50
   ```

   *(Or use `mockrelay replay --latency 50`.)*

2. Send the exact same request again:

   ```bash
   curl -i http://localhost:8080/gh/users/octocat
   ```

3. Notice the response headers:

   ```http
   X-MockRelay-Match: exact
   X-MockRelay-Fixture: gh-get-016c60e26e39
   X-MockRelay-Score: 4000009
   ```

The response is delivered entirely from your local JSON fixture without any
outbound network calls. You can prove it: stop the upstream, or turn off your
Wi-Fi, and run the suite again.

---

## 6. Inspect matching without a server

To see how MockRelay evaluates stored fixtures for a given request:

```bash
mockrelay match /users/octocat -u gh
```

```text
  hit  prio  strategy  score    status  id                   path
  ───────────────────────────────────────────────────────────────────────
  yes  0     exact     4000009  200     gh-get-016c60e26e39  /users/octocat [exact] vs /users/octocat

  ✓ winner gh-get-016c60e26e39 via exact (score 4000009, status 200)
  ✓ method: GET vs GET
  ✓ path: /users/octocat [exact] vs /users/octocat
```

Every candidate is listed with a per-check breakdown, so a miss tells you which
condition failed. `--json` gives the same information for a script.

---

## 7. Next steps

- Explore [Smart matching](matching.md) for wildcard, regex, fuzzy, and JSON body matching.
- Review [Operating modes](modes.md) to understand passthrough and hybrid workflows.
- Inspect the [Configuration reference](configuration.md) for header redaction and route overrides.
- Learn about the [Admin API & UI](admin.md) running at `http://localhost:8081`.
- Gate a pipeline on the fixture tree with [Recipes](recipes.md).
