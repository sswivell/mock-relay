# GitHub Discussion: welcome and feedback

Status: **submitted**
URL: https://github.com/sswivell/mock-relay/discussions/22
Category: Show and tell

Discussion categories already exist on the repo: Announcements, General, Ideas,
Q&A, Show and tell, Polls.

The repo had Discussions enabled with nothing in it, which reads as abandoned
to anyone evaluating whether to contribute or depend on the project. This post
is the fix, and it is an honest description of the current state rather than a
launch announcement.

## Title

```text
Introduce yourself, and tell me what you are mocking
```

## Body

```text
MockRelay is a local HTTP proxy that records real API traffic once and replays
it from JSON fixtures, so local development and integration tests do not
depend on a third-party API's uptime or rate limit.

Short version of how it works:

  mockrelay init
  mockrelay serve --mode record     # drive your app normally, traffic is saved
  mockrelay serve --mode replay     # same requests, served from disk, no network

Fixtures land in ./fixtures/<upstream>/*.json as plain JSON, with request and
response secrets redacted to {{SECRET}} before anything is written.

Current state, so you know what you are looking at:

- v1.0.0, one release, first published this week
- Python 3.10+, one runtime dependency (PyYAML)
- Not on PyPI yet. Publishing is the next thing being worked on, so the
  install is a git URL for now:

      pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

- Docs at https://sswivell.github.io/mock-relay/
- MIT licensed

What I would genuinely like help with, in rough order of how stuck I am:

1. **Ranking.** Fixtures are scored by path specificity band, then body and
   query constraint count, then literal density. I am not confident literal
   density is the right final tie-break. Has anyone hit a case where it picked
   the wrong fixture?

2. **Partial body matching ergonomics.** There are eleven operators. I suspect
   most people use three. Which ones earn their place and which are cruft?

3. **Fuzzy matching.** It is a separate band below regex, with a per-fixture
   threshold. Should it be opt-in per fixture rather than global?

4. **Recording ergonomics in real projects.** How do you decide what to record
   and what to hand-write? My current answer is "record everything once, prune
   with `mockrelay clean`", which I suspect is not what people actually do.

5. **Where this is the wrong tool.** I would like to hear that more than
   anything else. If you reached for this and something else was the right
   answer, I would like to know which and why, so I can say so in the README.

Questions, bug reports, and "this does not do the thing I need" are all
welcome, in Discussions or in issues. If you want to contribute, the issues
labelled good first issue are scoped to be finishable in one sitting.
```

## Why this shape

- Discloses the state honestly: one release, no PyPI, install is a git URL. A
  visitor who knows that up front is far more likely to trust everything else
  in the repo.
- Asks for criticism rather than stars. Asking for stars in a place full of
  developers is the fastest way to look like every other launch post.
- Question 5 is deliberate. A project that asks "where am I wrong" gets better
  feedback than one that asks "who wants to try this", and it signals that the
  maintainer is paying attention.