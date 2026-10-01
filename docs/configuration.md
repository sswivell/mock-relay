# Configuration

Full reference for mockrelay.yaml.

    listen: "127.0.0.1:8080"
    admin_listen: "127.0.0.1:8081"
    fixtures_dir: "./fixtures"
    mode: record
    latency_ms: 0
    metrics_enabled: true
    sequential: false

    # Smart matching
    match_mode: auto        # auto | exact | wildcard | regex | fuzzy
    fuzzy_threshold: 0.86   # 0.0 - 1.0
    ignore_case: false
    fuzzy_enabled: false    # allow fuzzy fallback for bare paths in auto mode
    smart_record_paths: true
    match_priority: [path, body, query, literal]   # see matching.md

    redact_headers:
      - authorization
      - cookie

    normalize_json_paths:
      - "$.id"

    upstreams:
      gh:
        base_url: "https://api.github.com"
        mode: record

## Matching settings

`match_mode`, `fuzzy_threshold`, `ignore_case`, `fuzzy_enabled`, and
`match_priority` can be set globally, per upstream, and per route. The most
specific definition wins, with route beating upstream beating global. See
[Smart matching](matching.md).

    upstreams:
      gh:
        base_url: "https://api.github.com"
        match_mode: wildcard
        fuzzy_threshold: 0.9
        routes:
          /v1/search:
            match_mode: fuzzy
            fuzzy_threshold: 0.8
            match_priority: [query, path, body, literal]

`routes` is a mapping of path prefix to overrides. The longest matching prefix
wins.

`smart_record_paths` is global only. When enabled, newly recorded fixtures
store the strategy prefix they matched with.

## Sequential replay

`sequential` switches fixture selection from ranking to cycling: matching
fixtures are served in ascending `call_index` order and the list wraps.

```yaml
sequential: true
```

It exists for endpoints that answer differently on each call — OAuth-style token
exchanges, pagination until empty, or a sequence of responses that has to be
reproduced in order.

Two consequences worth knowing before you turn it on:

- `match_priority` and per-fixture `priority` are ignored. Ordering is purely
  `call_index`.
- Recording does not produce a sequence for you. Fixture identity is derived
  from the request, so recording the same endpoint repeatedly overwrites one
  file instead of writing N. If the steps differ by query parameter or request
  body, leave `sequential` off and give each fixture an integer `priority`
  instead.

See [Sequential replay](matching.md#sequential-replay) for a worked example.

## Redaction and normalization

Both run before anything is written to disk, on the request side and the
response side.

`redact_headers` names the headers whose values are replaced with
`{{SECRET}}`. It is matched case-insensitively and applies to response
headers as well as request headers, so a token an upstream echoes back in
`x-api-key` does not land in the fixture.

`normalize_json_paths` lists JSON paths whose values are replaced with
`{{NORMALIZED}}`. Volatile values such as `$.id` and `$.created` would
otherwise make every recording differ from the last.

In addition, values that look like credentials are replaced wherever they
appear, in a header value or in a body string. This is a best-effort
filter, not a guarantee: no pattern list is complete. Review fixtures
before committing them.

    redact_headers:
      - authorization
      - cookie
      - x-api-key

    normalize_json_paths:
      - "$.id"
      - "$.created"
      - "$.request_id"

The request body, the response body, the response headers, and the match
spec are all written through the same filter, so a secret cannot leak
through matching metadata such as `body_contains`.
