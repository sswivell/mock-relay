# Awesome list and directory submissions

All verified 2026-09-30. One tool per submission, existing file format, no
multi-entry PRs. The rules for two of these explicitly reject coordinated
multi-entry self-promotion, which is also just good manners.

**Both PRs below have been opened.** Their current state is tracked in
[`README.md`](README.md).

---

## 1. cleder/awesome-python-testing — SUBMITTED

URL: https://github.com/cleder/awesome-python-testing/pull/129
Target section: `README.md` → `## Mock and Stub`

**Why it fits:** that section already contains Cornell ("record & replay mock
server") and Mockintosh. It is the closest category match that exists.

**What the repo actually does:** 312 stars, not archived, last commit
2026-09-29, four external entries merged in the two weeks to 2026-09-23. It
accepts new entries. Turnaround is roughly 1-5 days for the ones that get
merged; several recent PRs were closed unmerged, so it is selective.

**Rules:** there is no CONTRIBUTING.md. The convention from merged PRs is
strict: one tool per PR, strict alphabetical placement within the section (there
was a follow-up commit whose only purpose was "Place DriftWire in alphabetical
order"), and `- [Name](url) - Description.` with a full stop. `typos` and
`rumdl` lint run in pre-commit, so watch spelling and markdown lint.

**Placement used:** between `Mockintosh` and `moto`, which is where
`MockRelay` sorts alphabetically.

**PR title**

```text
Add MockRelay to Mock and Stub
```

**PR body**

```markdown
Adds [MockRelay](https://github.com/sswivell/mock-relay), a local HTTP proxy that
records real API traffic to JSON fixtures and replays them offline, with ranked
fixture matching so the most specific fixture wins rather than whichever file the
filesystem returned first.

Placed between `Mockintosh` and `moto` to keep the section alphabetical. One
tool, single entry, existing format.
```

**Exact line added**

```markdown
- [MockRelay](https://github.com/sswivell/mock-relay) - Local HTTP proxy that records real API traffic to JSON fixtures and replays them offline with ranked fixture matching.
```

**If it is rejected:** do not resubmit a variant. Close it and leave the note.
Reposting after a rejection is the behaviour that gets a project labelled as
self-promo spam.

---

## 2. marmelab/awesome-rest — SUBMITTED

URL: https://github.com/marmelab/awesome-rest/pull/230
Target section: `README.md` → `## Testing` → `### Mocking`

**Why it fits:** a pure mocking category, alongside FakeRest, json-server,
RequestBin, httpbin, MockServer, Mockoon, Mockintosh, Mockae. There is also a
`### Debugging Proxies` section with mitmproxy, Charles, and Fiddler, which is
arguably an equally good home for a recording proxy.

**What the repo actually does:** 3,918 stars, last push 2026-09-23, not
archived.

**Rules:** no CONTRIBUTING.md. The section uses `*` bullets rather than `-`,
entries end with a full stop, and **it is not alphabetised**. The entry was
therefore appended after `Mockae`, following the existing convention.

**Gotcha:** the default branch is `master`, not `main`. A PR targeting `main`
fails with "Base ref must be a branch".

**PR title**

```text
Add MockRelay to Mocking
```

**PR body**

```markdown
Adds [MockRelay](https://github.com/sswivell/mock-relay) to the `Mocking`
section: a local HTTP proxy that records real API traffic to JSON fixtures and
replays them offline, with ranked fixture matching so the most specific
response wins rather than whichever file the filesystem returned first.

Appended after `Mockae`. The section is not alphabetised, so this follows the
existing append-at-the-end convention.
```

**Exact line added**

```markdown
* [MockRelay](https://github.com/sswivell/mock-relay) - Local HTTP proxy that records real API traffic to JSON fixtures and replays them offline, with ranked fixture matching so the most specific response wins.
```

**Expect this to take a while.** The Mocking section has a visible backlog of
unmerged PRs: MockBase opened 2026-09-09, DriftWire 2026-09-22. So a wait of
weeks is normal here and is not a rejection. Leave it alone.

---

## 3. vinta/awesome-python — not yet

URL: https://github.com/vinta/awesome-python

Do not attempt this before MockRelay is on PyPI. The CONTRIBUTING.md rules are
explicit and a cold PR would be auto-closed:

- "max 3 obvious choices + 2 challengers per use case, hard max 5"
- "once a use case is at its cap, the only way in is to name the entry your
  project replaces"
- admission is decided "informed primarily by **PyPI download counts rather than
  GitHub stars**"
- structure changes are maintainer-only, so an entry PR cannot create the
  subcategory it needs
- automatic rejection for "coordinated multi-entry self-promotion"

The `- Mock` category is at cap with `vcrpy` as the incumbent. A displacement
argument against vcrpy is legitimate, because the two genuinely differ (proxy
versus client library, plain JSON fixtures versus cassette YAML, ranked
matching versus sequence playback). But it is a much stronger argument with a
real PyPI download number behind it. Publish to PyPI first, then revisit.

---

## 4. LibHunt — SUBMITTED

URL: https://www.libhunt.com/r/mock-relay
Form: https://www.libhunt.com/repo/submit → posts to `/repo/create`
Requires: a repo URL. No login.
Status: `submitted`. Accepted and indexed at
https://www.libhunt.com/repo/3893156/suggest_alternative

It already groups MockRelay with Hoverfly and similar service-virtualization
tools, which is the right neighbourhood. The full form was filled in:

| Field | Value |
|---|---|
| `repo[url]` | `https://github.com/sswivell/mock-relay` |
| `repo[name]` | `mock-relay` |
| `repo[description]` | Local HTTP proxy that records real API traffic to JSON fixtures and replays them offline with ranked fixture matching. For API testing, integration testing, and CI. |
| `repo[homepage_url]` | `https://sswivell.github.io/mock-relay/` |
| `repo[docs_url]` | `https://sswivell.github.io/mock-relay/` |
| `repo[is_selfhosted]` | `0` |
| `topics_list` | `http mocking,api mocking,record replay,testing,fixtures` |

Nothing to do again here. Do not resubmit.

---

## What not to submit to

| Target | Why |
|---|---|
| sindresorhus/awesome | Its PR template requires adding *another awesome list*, not a tool. Also rejects fully AI-generated PRs. |
| atinfo/awesome-test-automation | Last push 2025-11-28. Dormant. |
| elangosundar/awesome-api-tools | Last push 2022-11-06. |
| savkat/awesome-api | 0 stars, 0 forks, 0 commits. |
| InfoQ recommendations | 404. Editorial only. |
| awesomeopensource.com | No submission form could be verified. Third-party sites claiming one exists could not be confirmed. |
| libraries.io | Not a submission target; it scrapes PyPI. Publishing to PyPI is the real action. |
| OpenAlternative | Every entry is "Open Source Alternative to X", a proprietary product. Inventing a proprietary analogue for this would be dishonest framing. |
| Product Hunt | Launch-marketing channel, not developer discovery for a testing tool. |
| open-source.post, gitstar-ranking.com, newsletter.town | Unreachable at the time of checking. Check by hand if you care. |