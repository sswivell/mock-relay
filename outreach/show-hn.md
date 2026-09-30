# Show HN draft

Target: https://news.ycombinator.com/submit
Rules checked: 2026-09-30 against https://news.ycombinator.com/showhn.html,
https://news.ycombinator.com/newsguidelines.html, and
https://news.ycombinator.com/newsfaq.html

## Read this before you paste anything

HN's own guidelines say: "Don't post generated text or AI-edited text. HN is for
conversation between humans." dang's advice, linked from `showhn.html`, is
blunter: "Write your text by hand. Don't use an LLM to generate any of it (not
even a tiny bit, including to edit or spruce it up)."

So treat the text below as raw material, not as a finished submission. Read it,
throw away the parts that are not how you talk, and write the post yourself.
That is a requirement of the venue. A Show HN that reads like marketing copy
gets flagged, and a Show HN that reads like it was generated gets you a
moderation note.

What the draft is for is the structure and the technical content, both of
which are accurate.

## Title

Must begin with "Show HN".

```text
Show HN: MockRelay – a local HTTP proxy that records real API traffic and replays it as ranked JSON fixtures
```

Shorter alternative, if you prefer:

```text
Show HN: MockRelay – record real HTTP traffic once, replay it offline
```

## Body — write this in your own words

The backstory first. HN readers decide in about ten seconds whether to care,
and the first three lines are what they read. Then what it is, then the
technical part, which is the actual reason to engage.

```text
I kept losing local dev time to other people's uptime. A third-party sandbox
would go down or rate-limit the team, and the test suite would go red for
reasons that had nothing to do with the code under test. So I wanted the
recording part of VCR, but as a proxy rather than a library, with fixtures on
disk as plain JSON that could be read, diffed, and committed.

MockRelay is that: https://github.com/sswivell/mock-relay

You point your app at http://localhost:8080/<upstream>/... instead of the real
URL. In record mode it forwards upstream and writes each exchange to
fixtures/<upstream>/*.json. In replay mode it serves those files and makes no
outbound calls at all.

The part I found interesting to build was fixture selection. Most tools I've
used return the first fixture that matches, which means a broad wildcard can
shadow a specific route depending on the order the filesystem happened to
return files in. That's a flaky test that only reproduces on someone else's
machine.

MockRelay scores every candidate instead. Path strategy puts them in
specificity bands: exact > wildcard > regex > fuzzy. Then it adds body
constraint count, query constraint count, and literal character density. So
/users/42 always outranks /users/* no matter what is on disk.

Bodies match with operators rather than exact equality, which is what made the
case for ranking concrete:

  body_contains:
    status: paid
    total: { "$gt": 100 }
    $.items[*].sku: "wildcard:A*"

$eq, $ne, $gt, $gte, $lt, $lte, $in, $nin, $exists, $regex, $contains, with
JSONPath-style keys. Query matching is subset-based, so a fixture pins only the
params it cares about.

match_priority reorders the whole ranking, which came up for an API where a
query param identified the resource better than the path did:

  match_priority: [query, path, body, literal]

And mockrelay match shows the reasoning without starting a server:

  $ mockrelay match /orders/42 -m POST -b '{"total": 500}'
    hit  prio  strategy  score    status  id
    yes  0     exact     4002007  200     shop-exact-order-101
    yes  0     wildcard  3000008  200     shop-wildcard-orders
    no   0     miss      0        201     shop-post-order

Two things I had not thought about until I hit them: request AND response
bodies are redacted before a fixture is written, not just the request, so a
token in a response payload cannot get committed; and the match spec is built
from the redacted body, so a secret can't leak through a body constraint
either.

Python 3.10+, one runtime dependency (PyYAML), MIT. Install is a git URL
because I haven't published to PyPI yet:

  pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

Docs at https://sswivell.github.io/mock-relay/

I would rather hear where this is the wrong tool than where it fits. If your
problem is inventing responses that never happened, WireMock or Prism is a
better answer. This only helps when you have real traffic to capture.
```

## Notes on the draft

- The final paragraph is deliberate. `showhn.html` says a Show HN must be
  something you can try, and the guidelines say "Don't use HN primarily for
  promotion." Saying plainly where the tool does not apply is the single
  cheapest way to get useful replies instead of polite silence.
- No star count, no download count, no user count, because none of those are
  verified and the repo is new.
- Do not add a "would love stars" line. The guidelines ban soliciting upvotes.
- If you get traction, be in the thread. `showhn.html` requires that you are
  around to discuss it.
- Check https://news.ycombinator.com/shownew first. Every Show HN appears
  there, so you can see what is getting attention that morning and pick a slot
  where the topic is not already crowded.