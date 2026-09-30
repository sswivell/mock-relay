# MockRelay launch material

The prepared posts, the per-venue rules they are written against, and the
tracking table now live in [`outreach/`](outreach/). This file is kept as the
entry point and as the short version of the messaging.

Start with [`outreach/README.md`](outreach/README.md).

## Before you post

Two things to get right, because a broken install command is the first thing a
reader tries.

**1. Install.** MockRelay is not on PyPI. The command that works today is:

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

Once a PyPI release exists, `pip install mockrelay` is the shorter form and every
draft below reads better with it. Do not claim a PyPI release that does not
exist yet. The publish workflow is in `.github/workflows/publish.yml`; the
account setup is described in `outreach/README.md`.

**2. Links.** Both of these are live and can be used as-is:

- Site: <https://sswivell.github.io/mock-relay/>
- Release: <https://github.com/sswivell/mock-relay/releases/tag/v1.0.0>

### What is safe to claim, and what is not

Safe, because the test suite and `examples/matching_demo.py` demonstrate it:
the record/replay behaviour, the ranking order, the redaction, the body
operators, `match_priority`, and the CLI surface.

Not safe: adoption, stars, downloads, user counts, or any comparison to another
project. Do not add them, and do not add a "stars welcome" line. If a number
would be flattering but unverifiable, leave it out.

## Where each draft lives

| Channel | Draft |
|---|---|
| Hacker News Show HN | [`outreach/show-hn.md`](outreach/show-hn.md) |
| DEV technical article | [`outreach/dev-ranking.md`](outreach/dev-ranking.md) |
| Reddit (5 subreddits, one draft each) | [`outreach/reddit.md`](outreach/reddit.md) |
| Lobsters | [`outreach/lobsters.md`](outreach/lobsters.md) |
| GitHub Discussion | [`outreach/github-discussion.md`](outreach/github-discussion.md) |
| Newsletters and roundups | [`outreach/newsletters.md`](outreach/newsletters.md) |
| Awesome lists and directories | [`outreach/awesome-list-prs.md`](outreach/awesome-list-prs.md) |
| Answering other people's questions | [`outreach/answer-template.md`](outreach/answer-template.md) |
| Contributor onboarding issues | [`outreach/good-first-issues.md`](outreach/good-first-issues.md) |

## Angles, and where each one fits

Do not use the same pitch everywhere. Match the angle to what the audience is
actually there for.

| Angle | The pitch | Best venues |
|---|---|---|
| **API testing** | Testing against third-party APIs without hitting them every run | r/devops, console.dev, testing channels |
| **Local development** | Record real API traffic once, replay it locally | r/webdev, r/SideProject, DEV |
| **CI** | Deterministic HTTP fixtures for integration tests, and a `validate` gate | r/devops, PyCoder's Weekly |
| **Engineering** | Building a ranked fixture matcher for HTTP requests | Hacker News, DEV, Lobsters |
| **Open source** | A small HTTP record/replay proxy, looking for feedback | GitHub Discussions, r/opensource, Changelog |

The engineering angle is the one that works on Hacker News, DEV, and Lobsters,
because those audiences are reading for the idea rather than for the tool. The
open source angle is the one that works on the project's own repository.

## What has already been submitted

Recorded so nobody posts it twice:

- LibHunt: <https://www.libhunt.com/r/mock-relay>
- cleder/awesome-python-testing: <https://github.com/cleder/awesome-python-testing/pull/129>
- marmelab/awesome-rest: <https://github.com/marmelab/awesome-rest/pull/230>
- GitHub Discussion: <https://github.com/sswivell/mock-relay/discussions/22>
- Good first issues: <https://github.com/sswivell/mock-relay/issues/24>, <https://github.com/sswivell/mock-relay/issues/25>