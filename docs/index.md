---
title: MockRelay
description: Record real HTTP traffic once, replay it offline and deterministically. A local HTTP proxy with ranked fixture matching, redaction, and a CI-friendly CLI.
hide:
  - navigation
  - toc
---

# MockRelay

<div class="mr-hero">
  <div class="mr-badges">
    <span class="mr-badge mr-badge--accent"><span class="mr-badge-dot"></span> v1.0.0 &middot; stable</span>
    <span class="mr-badge">Python 3.10 &ndash; 3.13</span>
    <span class="mr-badge">Single dependency: PyYAML</span>
    <span class="mr-badge">MIT licensed</span>
  </div>

  <h1 class="mr-hero-title">Record real HTTP traffic once. <em>Replay it locally whenever you want.</em></h1>

  <p class="mr-hero-lede">
    MockRelay is a local HTTP proxy that records real API traffic into clean,
    redacted JSON fixtures and replays them offline and deterministically.
    Point your app at <code>:8080</code> in record mode, at replay mode
    tomorrow, and the responses are identical &mdash; no live network, no rate
    limits, no flaky sandbox.
  </p>

  <div class="mr-install">
    <div class="mr-install-code">
      <span class="mr-install-prompt">$</span>
      <span>pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"</span>
    </div>
    <button type="button" class="mr-copy" data-copy="pip install &quot;mockrelay @ git+https://github.com/sswivell/mock-relay.git&quot;"
            aria-label="Copy the MockRelay install command to clipboard">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <rect x="9" y="9" width="12" height="12" rx="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      <span class="mr-copy-label">Copy</span>
      <span class="mr-sr" role="status" aria-live="polite"></span>
    </button>
  </div>

  <p class="mr-install-note">
    Python 3.10&ndash;3.13, one runtime dependency. Not on PyPI yet &mdash; the
    command above installs the same tagged source as the release workflow.
  </p>

  <div class="mr-actions">
    <a class="mr-btn mr-btn--primary" href="getting-started/">
      Get started
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M5 12h14M13 6l6 6-6 6"></path>
      </svg>
    </a>
    <a class="mr-btn mr-btn--ghost" href="cli/">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="m4 17 6-5-6-5M12 19h8"></path>
      </svg>
      CLI reference
    </a>
    <a class="mr-btn mr-btn--ghost" href="matching/">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="7"></circle>
        <path d="m20 20-3.5-3.5"></path>
      </svg>
      How matching works
    </a>
    <a class="mr-btn mr-btn--ghost" href="https://github.com/sswivell/mock-relay"
       target="_blank" rel="noopener">
      <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38
                 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
                 -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
                 .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                 -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0
                 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
                 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
                 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"></path>
      </svg>
      GitHub
    </a>
  </div>
</div>

---

<section class="mr-section" id="workflow" data-reveal aria-labelledby="workflow-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">How it works</p>
    <h2 class="mr-section-title" id="workflow-title">One proxy, two jobs</h2>
    <p class="mr-section-lede">
      MockRelay sits between your application and the real services. In
      <strong>record</strong> mode it is a transparent proxy that writes a
      fixture for every exchange. In <strong>replay</strong> mode it never
      opens an outbound connection at all &mdash; it answers from the fixtures
      on disk.
    </p>
  </div>

  <div class="mr-flow">
    <div class="mr-flow-node">
      <span class="mr-flow-label">Your request</span>
      <span class="mr-flow-sub">GET http://localhost:8080/gh/users/octocat</span>
    </div>

    <div class="mr-flow-arrow">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 4v14M6 13l6 6 6-6"></path>
      </svg>
      <span>prefix selects the upstream</span>
    </div>

    <div class="mr-flow-node mr-flow-node--relay">
      <span class="mr-flow-label">MockRelay</span>
      <span class="mr-flow-sub">proxy :8080 &nbsp;&middot;&nbsp; admin :8081</span>
    </div>

    <div class="mr-flow-arrow">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M12 4v14M6 13l6 6 6-6"></path>
      </svg>
      <span>mode decides what happens</span>
    </div>

    <div class="mr-fork">
      <div class="mr-branch mr-branch--record">
        <span class="mr-branch-tag">record</span>
        <p class="mr-branch-text">
          Forward to the real upstream, redact the exchange, and write a
          fixture for it.
        </p>
        <span class="mr-fixture-chip">fixtures/gh/gh-get-016c60e26e39.json</span>
      </div>
      <div class="mr-branch mr-branch--replay">
        <span class="mr-branch-tag">replay</span>
        <p class="mr-branch-text">
          Rank every stored fixture, serve the most specific match. No socket
          is opened upstream.
        </p>
        <span class="mr-fixture-chip">X-MockRelay-Score: 4000009</span>
      </div>
    </div>
  </div>

  <div class="mr-mode-grid">
    <div class="mr-mode" data-mode="record">
      <p class="mr-mode-name">record</p>
      <p class="mr-mode-text">
        Every request is forwarded upstream and written to disk. Use it to
        capture real responses once.
      </p>
    </div>
    <div class="mr-mode" data-mode="replay">
      <p class="mr-mode-name">replay</p>
      <p class="mr-mode-text">
        Served from fixtures only. A request that matches nothing returns
        <code>501</code> naming the nearest candidates:
        <code>{"error": "no fixture matched", ..., "nearest": [...]}</code>.
      </p>
    </div>
    <div class="mr-mode" data-mode="passthrough">
      <p class="mr-mode-name">passthrough</p>
      <p class="mr-mode-text">
        Forwards upstream and records nothing. A plain proxy, for routes you
        do not want to capture.
      </p>
    </div>
    <div class="mr-mode" data-mode="hybrid">
      <p class="mr-mode-name">hybrid</p>
      <p class="mr-mode-text">
        Serves a fixture when one matches, otherwise goes upstream and records
        the result. Useful for growing a suite incrementally.
      </p>
    </div>
  </div>
</section>

---

<section class="mr-section" id="why" data-reveal aria-labelledby="why-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Why MockRelay</p>
    <h2 class="mr-section-title" id="why-title">Built for repeatability</h2>
    <p class="mr-section-lede">
      Most mock servers hand you a pile of JSON and hope you pick the right
      one. MockRelay records from real traffic, ranks what it finds, and keeps
      secrets out of what it writes.
    </p>
  </div>

  <div class="mr-reasons">
    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2 4 6v6c0 5 3.4 8.7 8 10 4.6-1.3 8-5 8-10V6l-8-4Z"></path>
          <path d="m9 12 2 2 4-4"></path>
        </svg>
      </span>
      <h3 class="mr-reason-title">Deterministic replay</h3>
      <p class="mr-reason-text">
        A fixture returns the same bytes every run, so a test that passed
        yesterday passes today. An upstream outage cannot turn your build red,
        and you stop spending a third party's rate limit on your own CI.
      </p>
    </div>

    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="9"></circle>
          <circle cx="12" cy="12" r="4.5"></circle>
          <circle cx="12" cy="12" r="1"></circle>
        </svg>
      </span>
      <h3 class="mr-reason-title">Ranked matching, not first-match</h3>
      <p class="mr-reason-text">
        Candidates are scored and sorted, not filtered in directory order.
        <code>/users/42</code> beats <code>wildcard:/users/*</code> no matter
        which file the filesystem hands back first.
      </p>
    </div>

    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 17V7a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v10"></path>
          <path d="M2 21h20M8 21v-4h8v4"></path>
        </svg>
      </span>
      <h3 class="mr-reason-title">Local development</h3>
      <p class="mr-reason-text">
        Your whole external API surface runs on <code>127.0.0.1</code>. Point
        the app at it once and keep working on a train, on a plane, or behind
        an outage.
      </p>
    </div>

    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M9 3H5a2 2 0 0 0-2 2v4M15 3h4a2 2 0 0 1 2 2v4M9 21H5a2 2 0 0 1-2-2v-4M15 21h4a2 2 0 0 0 2-2v-4"></path>
        </svg>
      </span>
      <h3 class="mr-reason-title">CI-friendly</h3>
      <p class="mr-reason-text">
        <code>mockrelay validate</code> checks the config and every fixture
        without starting a server, and exits <code>4</code> on a problem so a
        pipeline can gate on it. <code>--json</code> covers the rest.
      </p>
    </div>

    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6"></path>
        </svg>
      </span>
      <h3 class="mr-reason-title">Configurable</h3>
      <p class="mr-reason-text">
        Inject latency and <code>429</code>s to exercise retry and backoff,
        reorder what &ldquo;specific&rdquo; means with
        <code>match_priority</code>, and override settings per upstream or per
        route prefix.
      </p>
    </div>

    <div class="mr-reason">
      <span class="mr-reason-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round">
          <rect x="4" y="10" width="16" height="11" rx="2"></rect>
          <path d="M8 10V7a4 4 0 0 1 8 0v3"></path>
        </svg>
      </span>
      <h3 class="mr-reason-title">Safe to commit</h3>
      <p class="mr-reason-text">
        Request and response headers and bodies pass through redaction before
        anything is written, so tokens land on disk as
        <code>{{{{SECRET}}}}</code>. Volatile IDs become
        <code>{{{{NORMALIZED}}}}</code>, so recordings diff cleanly.
      </p>
    </div>
  </div>
</section>

---

<section class="mr-section" id="matching" data-reveal aria-labelledby="matching-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Matching</p>
    <h2 class="mr-section-title" id="matching-title">Path, query, and body &mdash; ranked, not guessed</h2>
    <p class="mr-section-lede">
      A fixture describes what it should answer: the method, the path, the
      query parameters it cares about, and the body fields it constrains. Every
      candidate is scored and the most specific one wins.
    </p>
  </div>

  <div class="mr-match">
    <div>
      <div class="mr-panel" style="margin-bottom: 1.25rem;">
        <div class="mr-panel-head">
          <span>What a fixture can constrain</span>
        </div>
        <div class="mr-panel-body">
          <ul class="mr-facet-list">
            <li class="mr-facet">
              <span class="mr-facet-name">path</span>
              <span class="mr-facet-body">
                <b>exact</b> <code>/users/7</code> &middot;
                <b>wildcard</b> <code>wildcard:/files/**</code> &middot;
                <b>regex</b> <code>re:^/orders/\d+$</code> &middot;
                <b>fuzzy</b> <code>fuzzy:/customer/prof</code>
              </span>
            </li>
            <li class="mr-facet">
              <span class="mr-facet-name">query</span>
              <span class="mr-facet-body">
                <code>query_subset: {"page": ["2"]}</code> &mdash; matches
                <code>?page=2&amp;sort=asc</code>, because only the parameters
                you name are compared.
              </span>
            </li>
            <li class="mr-facet">
              <span class="mr-facet-name">body</span>
              <span class="mr-facet-body">
                <code>body_contains</code> with <code>$gt</code>,
                <code>$in</code>, <code>$regex</code> and friends, keyed by
                plain names, <code>*</code>, or JSONPath like
                <code>$.items[*].sku</code>.
              </span>
            </li>
          </ul>
        </div>
      </div>

      <div class="mr-panel">
        <div class="mr-panel-head">
          <span>Specificity order</span>
        </div>
        <div class="mr-panel-body">
          <table class="mr-strategy-table">
            <thead>
              <tr>
                <th scope="col">Strategy</th>
                <th scope="col">Prefix</th>
                <th scope="col">Band</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><span class="mr-tag mr-tag--exact">exact</span></td>
                <td><code>exact:</code></td>
                <td>4 &mdash; wins</td>
              </tr>
              <tr>
                <td><span class="mr-tag mr-tag--wildcard">wildcard</span></td>
                <td><code>wildcard:</code> <code>glob:</code></td>
                <td>3</td>
              </tr>
              <tr>
                <td><span class="mr-tag mr-tag--regex">regex</span></td>
                <td><code>re:</code> <code>regex:</code></td>
                <td>2</td>
              </tr>
              <tr>
                <td><span class="mr-tag mr-tag--fuzzy">fuzzy</span></td>
                <td><code>fuzzy:</code></td>
                <td>1</td>
              </tr>
              <tr>
                <td><span class="mr-tag mr-tag--priority">priority</span></td>
                <td>per-fixture integer</td>
                <td>outranks all</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="mr-panel" data-rank-demo>
      <div class="mr-panel-head">
        <span>mockrelay match /orders/101 -m GET -u shop</span>
      </div>
      <div class="mr-term">
        <div class="mr-term-line">
          <span class="mr-term-h">hit</span>
          <span class="mr-term-h">strategy</span>
          <span class="mr-term-h">score</span>
          <span class="mr-term-h">fixture</span>
        </div>
        <div class="mr-term-line" data-strategy="exact" data-active="true"
             data-caption="Exact path: the highest band, so it outranks every other candidate for /orders/101.">
          <span class="mr-term-yes">yes</span>
          <span class="mr-term-c mr-term-exact">exact</span>
          <span class="mr-term-c">4000009</span>
          <span class="mr-term-c">shop-exact-order-101</span>
        </div>
        <div class="mr-term-line" data-strategy="wildcard" data-active="false"
             data-caption="A wildcard still matches, one band lower, so it is ranked below the exact fixture.">
          <span class="mr-term-yes">yes</span>
          <span class="mr-term-c mr-term-wildcard">wildcard</span>
          <span class="mr-term-c">3000008</span>
          <span class="mr-term-c">shop-wildcard-orders</span>
        </div>
        <div class="mr-term-line" data-strategy="regex" data-active="false"
             data-caption="The regex pattern matches too. It ranks lower, which is what you want.">
          <span class="mr-term-yes">yes</span>
          <span class="mr-term-c mr-term-regex">regex</span>
          <span class="mr-term-c">2000009</span>
          <span class="mr-term-c">shop-regex-orders</span>
        </div>
        <div class="mr-term-line" data-strategy="fuzzy" data-active="false"
             data-caption="Fuzzy tolerates the typo in /ordres/, so it matches — but only as a last resort.">
          <span class="mr-term-yes">yes</span>
          <span class="mr-term-c mr-term-fuzzy">fuzzy</span>
          <span class="mr-term-c">1000009</span>
          <span class="mr-term-c">shop-fuzzy-orders</span>
        </div>
        <div class="mr-term-line" data-strategy="miss" data-active="false"
             data-caption="wildcard:/files/** does not match /orders/101, so it is scored 0 and never served.">
          <span class="mr-term-no">no</span>
          <span class="mr-term-c mr-term-no">miss</span>
          <span class="mr-term-c">0</span>
          <span class="mr-term-c">shop-glob-files</span>
        </div>
        <div class="mr-term-line" data-strategy="miss" data-active="false"
             data-caption="The right path but the wrong method: POST /orders cannot answer a GET.">
          <span class="mr-term-no">no</span>
          <span class="mr-term-c mr-term-no">miss</span>
          <span class="mr-term-c">0</span>
          <span class="mr-term-c">shop-post-order</span>
        </div>
        <div class="mr-term-line">
          <span class="mr-term-c mr-term-win">&#10003; winner shop-exact-order-101 via exact</span>
        </div>
      </div>
      <p class="mr-rank-caption" data-rank-caption>
        Exact path: the highest band, so it outranks every other candidate for
        /orders/101.
      </p>
    </div>
  </div>

  <div class="mr-note">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10"></circle>
      <path d="M12 16v-4M12 8h.01"></path>
    </svg>
    <p>
      <code>match_priority</code> reorders the criteria globally, per upstream,
      or per route &mdash; put <code>query</code> first when a query parameter
      identifies the resource better than the path. A fixture can also carry an
      integer <code>priority</code> that outranks the criteria entirely. The
      output above is real <code>mockrelay match</code> output, not an
      illustration.
    </p>
  </div>
</section>

---

<section class="mr-section" id="quickstart" data-reveal aria-labelledby="quickstart-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Quick start</p>
    <h2 class="mr-section-title" id="quickstart-title">Recording your first fixture</h2>
    <p class="mr-section-lede">
      Four commands. The first one writes a config, the second records real
      traffic, and the last two replay it with the network switched off.
    </p>
  </div>

  <div class="mr-steps">
    <div class="mr-step">
      <div>
        <h3 class="mr-step-title">Install</h3>
        <p class="mr-step-text">Python 3.10 or newer.</p>
        ```bash
        pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
        ```
      </div>
    </div>

    <div class="mr-step">
      <div>
        <h3 class="mr-step-title">Write a config</h3>
        <p class="mr-step-text">
          <code>mockrelay init</code> creates a starter
          <code>mockrelay.yaml</code>. It refuses to overwrite an existing
          file unless you pass <code>--force</code>.
        </p>
        ```bash
        mockrelay init
        ```
      </div>
    </div>

    <div class="mr-step">
      <div>
        <h3 class="mr-step-title">Record</h3>
        <p class="mr-step-text">
          The first path segment picks the upstream: <code>/gh/...</code> goes
          to the <code>gh</code> entry in your config.
        </p>
        ```bash
        mockrelay serve --mode record

        # in another terminal
        curl http://localhost:8080/gh/users/octocat
        ```
      </div>
    </div>

    <div class="mr-step">
      <div>
        <h3 class="mr-step-title">Replay, offline</h3>
        <p class="mr-step-text">
          Stop the server, start it again in replay mode, and send the same
          request. It is answered from
          <code>fixtures/gh/gh-get-016c60e26e39.json</code>, and the response
          tells you which fixture won.
        </p>
        ```bash
        mockrelay serve --mode replay --latency 50

        curl -i http://localhost:8080/gh/users/octocat
        # HTTP/1.1 200 OK
        # X-MockRelay-Match: exact
        # X-MockRelay-Fixture: gh-get-016c60e26e39
        # X-MockRelay-Score: 4000009
        ```
      </div>
    </div>
  </div>
</section>

---

<section class="mr-section" id="config" data-reveal aria-labelledby="config-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Configuration</p>
    <h2 class="mr-section-title" id="config-title">A config that reads like the rest of your repo</h2>
    <p class="mr-section-lede">
      One YAML file, resolvable at three levels. A setting on a route beats
      the same setting on an upstream, which beats the global default.
    </p>
  </div>

```yaml
# mockrelay.yaml
listen: "127.0.0.1:8080"
admin_listen: "127.0.0.1:8081"
fixtures_dir: "./fixtures"
mode: record
latency_ms: 0

# What counts as the most specific match
match_mode: auto            # auto | exact | wildcard | regex | fuzzy
fuzzy_threshold: 0.86       # 0.0 - 1.0
ignore_case: false
match_priority: [path, body, query, literal]

# Applied to the request and the response before anything touches disk
redact_headers: [authorization, cookie, x-api-key]
normalize_json_paths: ["$.id", "$.created"]

upstreams:
  gh:
    base_url: "https://api.github.com"
    mode: record
    routes:
      # Only this prefix, and only this upstream, injects failures
      "/users/ada":
        mode: passthrough

  local:
    base_url: "http://localhost:9000"
    routes:
      "/v1/slow":
        latency_ms: 800
      "/v1/retry-test":
        error_injection:
          status: 429
          rate: 0.5          # half of these requests fail
```

A recorded fixture is a plain JSON file you can read, diff, and commit:

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

Point an existing client at it and nothing else changes:

```python
import httpx

client = httpx.Client(base_url="http://localhost:8080/gh")

response = client.get("/users/octocat")
response.status_code                    # 200
response.headers["X-MockRelay-Match"]    # "exact"
response.headers["X-MockRelay-Fixture"]  # "gh-get-016c60e26e39"
```
</section>

---

<section class="mr-section" id="features" data-reveal aria-labelledby="features-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Capabilities</p>
    <h2 class="mr-section-title" id="features-title">Everything in the box</h2>
  </div>

  <div class="mr-features">
    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M13 2 4 14h7l-1 8 9-12h-7l1-8Z"></path>
        </svg>
        Four operating modes
      </h3>
      <p class="mr-feature-text">
        record, replay, passthrough, hybrid &mdash; set globally, per upstream,
        or per route prefix.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 6h18M7 12h10M11 18h2"></path>
        </svg>
        Ranked matching
      </h3>
      <p class="mr-feature-text">
        exact, wildcard, regex, and fuzzy paths, scored by specificity rather
        than file order.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M16 3h5v5M4 20 21 3M21 16v5h-5M15 15l6 6M4 4l5 5"></path>
        </svg>
        JSON body matching
      </h3>
      <p class="mr-feature-text">
        <code>body_contains</code> with <code>$gt</code>, <code>$in</code>,
        <code>$regex</code>, <code>$exists</code> and JSONPath keys.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M4 6h16M4 12h10M4 18h7"></path>
        </svg>
        match_priority
      </h3>
      <p class="mr-feature-text">
        Reorder what specificity means, and pin a single fixture with an
        integer <code>priority</code>.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="4" y="10" width="16" height="11" rx="2"></rect>
          <path d="M8 10V7a4 4 0 0 1 8 0v3"></path>
        </svg>
        Redaction
      </h3>
      <p class="mr-feature-text">
        Header and body secrets become <code>{{SECRET}}</code> before the
        write; volatile fields become <code>{{NORMALIZED}}</code>.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="9"></circle>
          <path d="M12 7v5l3 2"></path>
        </svg>
        Latency &amp; fault injection
      </h3>
      <p class="mr-feature-text">
        Add delay or a <code>429</code> at a given rate, to prove your retry
        and backoff actually work.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="m4 17 6-5-6-5M12 19h8"></path>
        </svg>
        CLI
      </h3>
      <p class="mr-feature-text">
        <code>serve</code>, <code>record</code>, <code>replay</code>,
        <code>list</code>, <code>match</code>, <code>validate</code>,
        <code>stats</code>, <code>clean</code>, <code>init</code>,
        <code>config</code>.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M9 11 12 14 22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"></path>
        </svg>
        Validation
      </h3>
      <p class="mr-feature-text">
        <code>mockrelay validate</code> reports a bad setting or an unreadable
        fixture and exits <code>4</code>, so CI can fail on it.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M3 3v18h18"></path>
          <path d="m7 14 3-4 3 3 5-7"></path>
        </svg>
        Stats &amp; cleanup
      </h3>
      <p class="mr-feature-text">
        <code>stats</code> counts what is recorded; <code>clean</code> previews
        then prunes fixtures older than a cutoff.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M16 18 22 12 16 6M8 6 2 12l6 6"></path>
        </svg>
        JSON output
      </h3>
      <p class="mr-feature-text">
        <code>--json</code> on the inspection commands, with a
        <code>schema</code> version and documented exit codes.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="16" rx="2"></rect>
          <path d="M3 9h18"></path>
        </svg>
        Admin API &amp; metrics
      </h3>
      <p class="mr-feature-text">
        A dashboard, <code>/api/match</code>, and Prometheus
        <code>/metrics</code> on <code>:8081</code>.
      </p>
    </div>

    <div class="mr-feature">
      <h3 class="mr-feature-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M20 6 9 17l-5-5"></path>
        </svg>
        No cloud, no account
      </h3>
      <p class="mr-feature-text">
        A local process and a directory of JSON. Nothing is uploaded anywhere.
      </p>
    </div>
  </div>
</section>

---

<section class="mr-section" id="docs" data-reveal aria-labelledby="docs-title">
  <div class="mr-section-head">
    <p class="mr-eyebrow">Documentation</p>
    <h2 class="mr-section-title" id="docs-title">Read the reference</h2>
    <p class="mr-section-lede">
      Every flag, config key, header, and exit code is documented. Start with
      getting started, or go straight to the reference you need.
    </p>
  </div>

  <div class="mr-docs">
    <p class="mr-doc-card-group">Start here</p>

    <a class="mr-doc-card" href="getting-started/">
      <span class="mr-doc-card-name">
        Getting started
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Install, configure, and run your first record and replay cycle.</p>
    </a>

    <a class="mr-doc-card" href="modes/">
      <span class="mr-doc-card-name">
        Operating modes
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">What record, replay, passthrough, and hybrid each do.</p>
    </a>

    <a class="mr-doc-card" href="fixtures/">
      <span class="mr-doc-card-name">
        Fixtures &amp; redaction
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">The fixture schema, secret masking, and per-fixture overrides.</p>
    </a>

    <a class="mr-doc-card" href="recipes/">
      <span class="mr-doc-card-name">
        Recipes
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">SDK redirection, retry testing, CI gating, and pruning.</p>
    </a>

    <p class="mr-doc-card-group">Reference</p>

    <a class="mr-doc-card" href="cli/">
      <span class="mr-doc-card-name">
        CLI reference
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Every command and flag, plus the JSON schema and exit codes.</p>
    </a>

    <a class="mr-doc-card" href="configuration/">
      <span class="mr-doc-card-name">
        Configuration
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Every key in mockrelay.yaml, defaults, and scoped overrides.</p>
    </a>

    <a class="mr-doc-card" href="matching/">
      <span class="mr-doc-card-name">
        Smart matching
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Strategies, body operators, priority, and how to debug a miss.</p>
    </a>

    <a class="mr-doc-card" href="admin/">
      <span class="mr-doc-card-name">
        Admin API
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">The dashboard, the JSON endpoints, and the metrics format.</p>
    </a>

    <a class="mr-doc-card" href="architecture/">
      <span class="mr-doc-card-name">
        Architecture
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Module map, request flow, and how ranking is actually computed.</p>
    </a>

    <p class="mr-doc-card-group">Project</p>

    <a class="mr-doc-card" href="demo/">
      <span class="mr-doc-card-name">
        Demo script
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">A scripted end-to-end run using the bundled example upstream.</p>
    </a>

    <a class="mr-doc-card" href="development/">
      <span class="mr-doc-card-name">
        Development
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
             stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M5 12h14M13 6l6 6-6 6"></path>
        </svg>
      </span>
      <p class="mr-doc-card-text">Local setup, the test suite, linting, and building the docs.</p>
    </a>
  </div>
</section>

---

<section class="mr-section" data-reveal aria-labelledby="project-title">
  <div class="mr-cta">
    <div>
      <h2 class="mr-cta-title" id="project-title">Open source, and it stays that way</h2>
      <p class="mr-cta-text">
        MockRelay is MIT licensed. Issues, bug reports, and pull requests are
        all welcome &mdash; the honest way to say it is that this is a small
        tool built by one person, and that shaped a lot of the design.
      </p>
      <div class="mr-actions">
        <a class="mr-btn mr-btn--primary" href="https://github.com/sswivell/mock-relay"
           target="_blank" rel="noopener">
          <svg viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
            <path d="M8 0C3.58 0 0 3.58 0 8a8 8 0 0 0 5.47 7.59c.4.07.55-.17.55-.38
                     0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13
                     -.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66
                     .07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15
                     -.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0
                     1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82
                     1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01
                     1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8Z"></path>
          </svg>
          View on GitHub
        </a>
        <a class="mr-btn mr-btn--ghost" href="https://github.com/sswivell/mock-relay/issues"
           target="_blank" rel="noopener">Report an issue</a>
        <a class="mr-btn mr-btn--ghost" href="getting-started/"
           >Install guide</a>
      </div>
    </div>

    <dl class="mr-cta-side">
      <div class="mr-fact">
        <dt>License</dt>
        <dd>MIT</dd>
      </div>
      <div class="mr-fact">
        <dt>Python</dt>
        <dd>3.10 &ndash; 3.13</dd>
      </div>
      <div class="mr-fact">
        <dt>Runtime deps</dt>
        <dd>PyYAML</dd>
      </div>
      <div class="mr-fact">
        <dt>Install</dt>
        <dd><code>pip install "mockrelay @ git+…"</code></dd>
      </div>
      <div class="mr-fact">
        <dt>Source</dt>
        <dd><a href="https://github.com/sswivell/mock-relay" target="_blank" rel="noopener">github.com/sswivell/mock-relay</a></dd>
      </div>
    </dl>
  </div>
</section>
