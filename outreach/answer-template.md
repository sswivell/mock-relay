# Answering other people's questions

This is the highest-value version of outreach and the easiest to get wrong.
An answer that reads like an advertisement gets deleted, gets a warning, and
gets you removed from the community. An answer that solves the problem gets you
reputation, and the tool mention rides along.

## The rules

1. **Answer the question first and completely.** If the tool is more than one
   paragraph of the answer, the answer is wrong.
2. **Say plainly that you wrote it.** Immediately. Not buried at the bottom.
3. **If MockRelay does not fit, say so and suggest what does.** See the
   template below; this is not a formality, it is the part that makes the
   recommendation credible.
4. **Never paste the same reply into two threads.** Even paraphrased. That is
   comment spam with a helpful hat on.
5. **Do not go looking for threads to insert the name into.** Answering a
   question you searched for is astroturfing. Find the thread first, decide
   whether the answer is genuinely useful, and only then decide whether to
   mention the tool.
6. **Stay in the thread.** If someone asks a follow-up and the honest answer is
   "no, that does not do it", say that.
7. **Do not DM anyone.** No mass DMs, ever.

## Where to look

Search terms that indicate someone with a real problem:

```text
"how do I mock" "third-party API" tests
"record HTTP" fixtures tests
"test against API" "without hitting"
"replay" "API responses" test fixtures
"deterministic" API tests CI
"rate limit" CI tests "third party"
vcrpy vs "hand-written mocks"
"integration tests" "external API" flaky
mitmproxy OR WireMock "local development"
"stub" "external service" "unit test" Python
```

Good places: r/devops, r/Python, r/webdev, Stack Overflow, lobste.rs comments,
the `_qa`/testing channels on the usual developer Discords, and the comment
sections on posts about flaky integration tests.

Note that r/softwaretesting removes commercial tool links, and r/Python
requires showcase posts to go in the monthly thread. Read the rules before you
reply in either.

## Template: when MockRelay fits

```text
Full disclosure: I maintain MockRelay, so take that into account.

For what you describe, the usual options are:

- Client-layer recording, which is what vcrpy does. Good if the whole thing
  runs in one Python process and you control the client.
- A hand-written mock server, which is what responses/respx or a small
  aiohttp app give you.
- A shared sandbox, which works until it is someone else's problem.

A third option if you want the fixtures to live on disk and be reusable across
processes and across languages: a local recording proxy. Point your app at
the proxy, record once against the real service, then replay from files.

    pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
    mockrelay init
    mockrelay serve --mode record     # drive the app normally
    mockrelay serve --mode replay     # same requests, no network

Fixtures land in ./fixtures/<upstream>/*.json as plain JSON with secrets
redacted, so they diff and can be committed. Replay is deterministic, and
`mockrelay validate` exits 4 on a broken fixture so CI can gate on it.

The reason I mention it: [specific to THEIR problem — rate limits, the CI
flake, the cross-language client]. If [their situation] is the deciding factor
for you, this would not help and [alternative] would.
```

## Template: when it does not fit

Use this more often than the first one. It is the version that builds
reputation.

```text
I maintain a tool in this space (MockRelay, https://github.com/sswivell/mock-relay),
but it is probably not what you want here, and I'd rather tell you that than
sell you the wrong thing.

You are trying to [their actual situation]. That needs responses that never
happened, or need to change per test run, which means the source of truth
should be a spec rather than a recording. For that:

- WireMock or Prism if you want to stand up a mock server from an OpenAPI spec.
- responses or respx if you want to stub one client's responses in-process and
  nothing else.
- A fixture library for your test framework if the surface is not HTTP.

Where a recording proxy does win is when you need the real response shape,
offline, across processes. If that is your actual problem rather than the one
you described, say so and I will go into more detail.
```

## What not to write

- "You should check out my project." Nobody wants to be sent to a repo from a
  stranger in a thread about something else.
- "Hope this helps! Let me know if you want to try my tool." This is the
  pattern that gets accounts blocked.
- A comparison table written to make MockRelay win. If someone asks "is X or Y
  better" and you have a stake in one of the answers, say what you have used
  and what they are actually good at, and let them decide.
- Any number about stars, users, downloads, or companies. Not one of those is
  verified, and someone will check.