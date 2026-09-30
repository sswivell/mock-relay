# Operating Modes

MockRelay supports four distinct operational modes designed to accommodate different stages of the development and testing lifecycle.

---

## Mode Summary

| Mode | Upstream Forwarding | Local Fixture Replay | Disk Recording | Typical Use Case |
|---|---|---|---|---|
| **`record`** | Always | No | Writes all requests/responses | Initial setup & capturing new API endpoints |
| **`replay`** | Never | Yes (offline) | None | Local development, offline work, CI test suites |
| **`passthrough`** | Always | No | None | Transparent proxying without creating fixtures |
| **`hybrid`** | Only on fixture miss | Yes (on hit) | Records on miss only | Incremental test building without cold recording |

---

## 1. Record Mode (`record`)

In **record mode**, every request reaching MockRelay is forwarded to the configured upstream base URL. When the response arrives from upstream:

1. Both the request and response pass through the redaction and normalization filters.
2. A deterministic JSON fixture file is created under `fixtures/<upstream>/<fixture-id>.json`.
3. The response is forwarded back to your client application.

```bash
# Start proxy in record mode
mockrelay serve --mode record

# Or use the shorthand command
mockrelay record
```

!!! tip "Automatic Redaction"
    Headers listed in `redact_headers` (such as `Authorization` or `x-api-key`) and secret-shaped tokens are replaced with `{{SECRET}}` before anything touches disk.

---

## 2. Replay Mode (`replay`)

In **replay mode**, MockRelay operates entirely offline. It matches incoming requests against stored JSON fixtures using the [smart matching engine](matching.md).

- No outbound HTTP requests are ever made.
- If a matching fixture is found, it is returned with diagnostic headers:
  - `X-MockRelay-Match`: Strategy that won (`exact`, `wildcard`, `regex`, or `fuzzy`)
  - `X-MockRelay-Fixture`: ID of the winning fixture
  - `X-MockRelay-Score`: Diagnostic specificity score
- If no fixture matches, MockRelay returns HTTP `501 Not Implemented` with a diagnostic JSON payload indicating candidate distance and the active `match_mode`.

```bash
# Start proxy in replay mode with artificial delay
mockrelay serve --mode replay --latency 50

# Or shorthand
mockrelay replay --latency 150
```

---

## 3. Passthrough Mode (`passthrough`)

In **passthrough mode**, MockRelay acts as a standard forwarding HTTP proxy.

- Requests are proxied directly to the upstream server.
- No fixture files are created or read.
- Useful for diagnosing issues against live services or for routes where recording is explicitly unwanted.

```bash
mockrelay serve --mode passthrough
```

---

## 4. Hybrid Mode (`hybrid`)

In **hybrid mode**, MockRelay attempts to serve incoming requests from stored fixtures first.

- **On Match Hit:** The response is served directly from the local fixture (fast, offline).
- **On Match Miss:** MockRelay forwards the request upstream to the live server, returns the response, and records a new fixture on disk.

This mode allows incrementally building out a test suite without requiring an explicit, dedicated recording phase.

```bash
mockrelay serve --mode hybrid
```

---

## Mode Overrides

The mode for a request is resolved from the config before anything is
forwarded. The longest matching route prefix wins, then the upstream, then
the global default:

```text
Per-Route Override  >  Per-Upstream Setting  >  Global Setting
```

### Per-Upstream and Per-Route Overrides

You can declare default modes per upstream service and override specific path prefixes in `mockrelay.yaml`:

```yaml
mode: replay  # Global default

upstreams:
  stripe:
    base_url: "https://api.stripe.com"
    mode: replay  # Replay all Stripe calls
  local:
    base_url: "http://localhost:9000"
    mode: passthrough  # By default pass through to local backend
    routes:
      "/v1/payments":
        mode: record  # Record only payment calls
```

A per-upstream or per-route `mode` takes precedence over the `--mode` flag on
the command line, because it is the more specific setting. Leave `mode` off an
upstream to let the flag and the global default apply.

### Switching a Running Server

The mode of a running server can be changed without a restart over the admin
API:

```bash
curl -X POST http://localhost:8081/api/mode/hybrid
```

See [Admin API & UI](admin.md).
