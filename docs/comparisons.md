# Comparisons

There are a lot of HTTP mocking tools. This page is an honest attempt to say
where MockRelay sits among the ones people actually reach for, and where it
does not.

None of these tools are bad. They solve different problems, and picking the
wrong one costs an afternoon.

## By shape

| Tool | Shape | What it is good at |
|---|---|---|
| **MockRelay** | Local HTTP proxy, records real traffic to JSON fixtures, replays offline | Development and integration tests against real API shapes |
| `vcrpy` | Library that patches the HTTP client | Recording inside one Python process |
| `responses` | Library that stubs one client's responses | Unit tests needing a canned response, no server |
| `respx` | Library that mocks `httpx` | The same, with first-class `httpx` support |
| `pytest-recording` | pytest fixture wrapping `vcrpy` | Cassettes for a pytest suite |
| WireMock | Standalone mock server, configured by hand or spec | Contract mocking, request verification |
| MockServer | Standalone mock server, Java and .NET | Service virtualisation with stateful scenarios |
| Prism | Contract mock from an OpenAPI document | Mocking straight from your spec |
| Hoverfly | Go proxy with a rules DSL | Service virtualisation and capture |
| mitmproxy | Interactive proxy, flow-based | Inspecting and modifying live traffic |

## The three questions that decide it

**Does the response need to have happened?**

MockRelay replays traffic that was really recorded. If you need to invent
responses, generate them from a spec, or produce them procedurally, MockRelay
is the wrong tool. Use Prism from an OpenAPI document, or WireMock.

**Does everything run in one process?**

MockRelay runs as a server. `responses`, `respx`, and `vcrpy` do not, which is
usually simpler when you can get away with it, and always faster to set up. They
are the right default for a Python unit test.

A server is the right answer when the transport cannot be intercepted: an SDK
that installs its own transport, a non-Python service, a multi-process test
run, or a browser driving your frontend.

**Do you need to see why a response was chosen?**

MockRelay answers this on every replayed response:

```http
X-MockRelay-Match: exact
X-MockRelay-Fixture: gh-get-016c60e26e39
X-MockRelay-Score: 4000009
```

And `mockrelay match <path>` prints the same reasoning without starting a
server. Cassette libraries report which cassette matched; they generally do not
rank candidates.

## Where MockRelay is genuinely different

### Ranked matching instead of first-match-wins

Record both `/users/42` and `wildcard:/users/*`, then request `/users/42`. What
happens?

Most record/replay tools return the first fixture that matches. Which one that
is depends on directory iteration order, and that is not stable across
operating systems, filesystems, or a fresh checkout. The result is a test that
passes on your machine and fails in CI for reasons unrelated to your change.

MockRelay scores every candidate. Path strategy sets a band — `exact` above
`wildcard` above `regex` above `fuzzy` — then body and query constraint count,
then literal density. File order is not part of the key, so it cannot influence
the result.

See [Smart matching](matching.md).

### Plain JSON on disk

Fixtures are ordinary JSON files in a directory you control:

```text
fixtures/gh/gh-get-016c60e26e39.json
```

They diff cleanly, they can be hand-edited, and they can be read without
running the tool. Cassettes are usually YAML or binary formats that need a
library to inspect.

### Validation as a CI gate

```bash
mockrelay validate
```

Loads a config and every fixture without starting a server or touching the
network, and exits `4` on a problem so a pipeline can gate on it. A
hand-edited fixture with the wrong shape fails with the file and the reason,
rather than as an unexplained `501` mid-suite.

### Nothing to deploy

A Python package with one dependency. It binds two local ports and runs against
your working directory. There is no service, no daemon, and no account.

## Where MockRelay loses

- **Cold start is higher.** `responses` is three lines in a fixture. MockRelay
  is a server you start, configure, and point at.
- **It cannot invent responses.** This is the big one, and it is not fixable
  within the design: the source of truth is a recording.
- **Fewer matchers than WireMock or Hoverfly.** You get path strategies, query
  subset matching, body operators, and priorities. You do not get a full rules
  DSL, stateful behaviour, or fault injection beyond latency and error rate.
- **The recorder does not capture multi-response sequences.** Recording the
  same endpoint twice overwrites one fixture. Sequential replay exists, but you
  write the sequence by hand.
- **Python only as an implementation.** The proxy itself is language-agnostic
  and any HTTP client can use it, but the CLI, admin UI, and fixture tooling
  are Python.

## If you are not sure

Try the cheapest thing that could work first:

1. You are writing a Python unit test → `responses` or `respx`.
2. You want to replay a real conversation in a pytest suite → `vcrpy` or
   `pytest-recording`.
3. You have an OpenAPI document → `Prism`.
4. You need to inspect live traffic → `mitmproxy`.
5. You need responses that never happened → `WireMock`.
6. You need real recorded responses, offline, across processes and languages →
   MockRelay.

If (6) is not your situation, one of the other five is a better fit and you
should use it.