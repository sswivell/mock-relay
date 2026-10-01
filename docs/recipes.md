# Common Recipes & Patterns

Practical configurations and workflows for everyday development and CI testing.

---

## 1. Record Once, Replay Forever with Demo Upstream

Run a mockable upstream server and capture fixtures locally:

```bash
# Terminal 1: Start the sample upstream
python examples/demo_upstream.py

# Terminal 2: Start MockRelay in record mode
mockrelay serve --mode record

# Terminal 3: Query the proxy
curl http://localhost:8080/local/v1/users

# Switch MockRelay to replay mode
mockrelay replay --latency 100

# Query again — now served offline from the fixture
curl http://localhost:8080/local/v1/users
```

---

## 2. Pointing Client SDKs at MockRelay

Redirect your application's API clients to MockRelay by configuring base URL environment variables.

### Stripe Python SDK
```bash
export STRIPE_API_BASE=http://localhost:8080/stripe
```

```python
import stripe
stripe.api_base = "http://localhost:8080/stripe"
```

### GitHub API / Octokit / HTTPX
```python
import httpx

client = httpx.Client(base_url="http://localhost:8080/gh")
resp = client.get("/users/octocat")
```

---

## 3. Testing Retry and Backoff Logic (Error Injection)

Inject transient errors (e.g. HTTP 429 Too Many Requests or 503 Service Unavailable) on specific routes to verify client retry and circuit breaker logic:

```yaml
upstreams:
  stripe:
    base_url: "https://api.stripe.com"
    mode: replay
    routes:
      "/v1/charges":
        error_injection:
          status: 429
          rate: 0.5  # 50% of requests return 429
```

---

## 4. Simulating Slow Upstreams and Network Latency

Test timeouts or loading spinners by adding artificial delay to all requests or specific routes:

Globally across all routes:
```bash
mockrelay replay --latency 1500
```

Or configure specific slow routes in `mockrelay.yaml`:
```yaml
upstreams:
  local:
    base_url: "http://localhost:9000"
    mode: replay
    routes:
      "/v1/export":
        latency_ms: 3000
```

---
## 5. Gating CI Pipelines on Fixture & Config Integrity

Add `mockrelay validate` to your continuous integration workflow. It verifies
that `mockrelay.yaml` is valid and that every fixture file can be parsed cleanly:

```bash
mockrelay validate || exit 1
```

Or output machine-readable JSON for CI step parsing:

```bash
mockrelay validate --json
```

### A complete GitHub Actions workflow

`validate` on its own only tells you the fixtures are readable. To actually run
the suite against the proxy you need three more things: start it in replay
mode, wait until it is listening rather than sleeping a fixed amount, and tear
it down so the job does not hang on the background process.

```yaml
# .github/workflows/integration.yml
name: integration

on: [push, pull_request]

jobs:
  replay:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"

      - run: python -m pip install --upgrade pip
      - run: pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
      - run: pip install pytest

      # Gate on fixture integrity before anything depends on it. Exits 4 on a
      # bad config or an unreadable fixture.
      - run: mockrelay validate

      - name: Start the proxy in replay mode
        run: |
          mockrelay replay --latency 0 &
          echo "MOCKRELAY_PID=$!" >> "$GITHUB_ENV"

      # Wait on the admin port rather than sleeping, so the job is not flaky
      # on a slow runner.
      - name: Wait for the admin port
        run: |
          for _ in $(seq 1 30); do
            if curl -sf http://127.0.0.1:8081/api/match?path=/ping >/dev/null; then
              echo "mockrelay is up"
              exit 0
            fi
            sleep 1
          done
          echo "mockrelay did not start in time" >&2
          exit 1

      - run: python examples/ci_replay.py

      - name: Stop the proxy
        if: always()
        run: kill "$MOCKRELAY_PID" || true
```

Two details worth keeping:

- `mockrelay validate` runs **before** the suite, so a hand-edited fixture fails
  with the file and the reason instead of turning into an unexplained `501` in
  the middle of a test run.
- The readiness check polls the admin port on `8081`. A fixed `sleep 2` works
  locally and fails intermittently on a loaded CI runner.

---

## 6. Prioritizing Query Parameters Over Paths

In APIs where the endpoint path is generic (e.g. `/api/v1/search`) and query parameters distinguish the response:

```yaml
upstreams:
  search:
    base_url: "https://api.example.com"
    match_priority: [query, path, body, literal]
```

This ensures a fixture specifically matching `?type=article` beats an exact path match lacking query constraints.

---

## 7. Managing and Pruning Fixtures

Inspect stored fixtures:
```bash
mockrelay stats
```

Preview fixtures older than 30 days:
```bash
mockrelay clean --older-than 30
```
Actually delete stale fixtures:

```bash
mockrelay clean --older-than 30 --yes
```

Without `--yes` the command only previews, and its `--json` output reports
`"dry_run": true`.

---

## 8. Inspecting a Live Server

The admin server on `admin_listen` (default `127.0.0.1:8081`) exposes the same
matching engine over HTTP, so you can ask it what a request would do without
sending that request:

```bash
curl "http://127.0.0.1:8081/api/match?method=GET&path=/users/7"
```

See [Admin API & UI](admin.md) for the full endpoint list.
