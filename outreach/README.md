# Outreach tracker

Everything here is a real, verifiable opportunity to put MockRelay in front of
developers who actually need HTTP mocking, API recording, or deterministic HTTP
replay. Nothing in this file or in `outreach/` was faked, and nothing here
should be posted without reading the target's current rules first.

Rules change. The "rules checked" column records when a rule set was verified,
and every row should be re-checked before you post.

## House rules

These are the constraints this project holds itself to. They are not
suggestions; they are the reason the outreach is credible.

- No fabricated metrics. No star counts, download counts, user counts, company
  names, testimonials, or press coverage unless a real number backs them.
- No stars-for-hire, no vote rings, no sockpuppets, no astroturfing, no
  cross-community copy-paste of the same post.
- No mass submissions to directories that do not curate. Quality over volume.
- Every post says plainly that the author built the thing. No pretending to be
  an unrelated developer recommending it.
- Disclose the affiliation in the first line of any post about MockRelay.
- Never bypass a CAPTCHA, a rate limit, or an anti-spam control.

## Status vocabulary

| Status | Meaning |
|---|---|
| `researched` | Rules located and read; nothing written yet |
| `drafted` | Text written and ready for review |
| `ready` | Reviewed, tailored to the target's rules, ready to post |
| `submitted` | Actually submitted — with the URL recorded |
| `approved` | Accepted and live |
| `rejected` | Submitted and refused; do not resubmit |
| `manual` | Needs your account, a login, or a human judgement call |
| `skip` | Deliberately not doing this, and why |

---

## 1. High value

### 1a. PyPI — the single highest-leverage item

| Field | Value |
|---|---|
| Platform | PyPI |
| Opportunity | Publish `mockrelay` to PyPI |
| URL | https://pypi.org/project/mockrelay/ |
| Rules | PyPI name policy: names must be unique, must not conflict, `mockrelay` was available on 2026-09-30 (`https://pypi.org/pypi/mockrelay/json` returned 404, i.e. no project) |
| Login required | Yes — your PyPI account |
| Approval required | Yes — first upload of a new project requires 2FA or a pending publisher |
| Status | **`manual`** — workflow is written, the account setup is yours |

Why this outranks everything else: the current install command is

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
```

That is a real conversion tax. It requires git, it builds from source, and it
reads as "this is a hobby repo, be careful" to anyone evaluating it. Compare it
to `pip install mockrelay`.

It also gates two other opportunities: `vinta/awesome-python` ranks candidates
primarily by **PyPI download counts**, and `libraries.io` indexes PyPI
automatically.

**What has been done for you:** `.github/workflows/publish.yml` builds the
sdist and wheel, runs the full test matrix and ruff first, and publishes with
PyPI **trusted publishing** (OIDC, short-lived token, no API token stored in the
repository).

**What you need to do:**

1. Create the project at https://pypi.org/manage/account/project/ with the name
   `mockrelay`.
2. Create a GitHub environment named `pypi` on the repository
   (Settings → Environments).
3. On PyPI, add a pending publisher for
   `sswivell/mock-relay`, workflow `publish.yml`, environment `pypi`.
4. Update the release workflow trigger if you prefer tags over releases, then
   publish a release. The `pypi` job runs on release publication.
5. Once it lands, `pip install mockrelay` works. Then change the install block
   in `README.md`, `docs/index.md`, and `docs/getting-started.md` from the git
   URL to the PyPI name and delete the "not on PyPI yet" notes. Those notes are
   deliberately still in place — claiming a PyPI release that does not exist
   would be a lie in your own README.

### 1b. Hacker News — Show HN

| Field | Value |
|---|---|
| Platform | Hacker News |
| Opportunity | `Show HN` |
| URL | https://news.ycombinator.com/submit |
| Rules checked | 2026-09-30 |
| Rules source | https://news.ycombinator.com/showhn.html, https://news.ycombinator.com/newsguidelines.html, https://news.ycombinator.com/newsfaq.html |
| Login required | Yes |
| Status | `drafted` — see `outreach/show-hn.md` |

The current rules, which the draft is written to respect:

- Title must begin with `Show HN`.
- It must be something you built personally and are around to discuss.
- Off topic as a Show HN: blog posts, sign-up pages, newsletters, lists, and
  other reading material. "Those can't be tried out, so can't be Show HNs."
- "Don't post quickly-generated one-offs."
- No sign-up or email gates.
- "Please don't ask friends to upvote or comment. That's not ok on HN."
- From the guidelines: "Don't post generated text or AI-edited text. HN is for
  conversation between humans." **This is the important one.** The draft in
  `outreach/show-hn.md` is written to be read and rewritten by you, not pasted
  verbatim. Rewriting it in your own words is a requirement of the venue, not
  an optional courtesy.
- dang's advice, linked from `showhn.html`
  (https://news.ycombinator.com/item?id=22336638): "Write your text by hand.
  Don't use an LLM to generate any of it (not even a tiny bit, including to
  edit or spruce it up)." Also: put the backstory at the top, say plainly what
  the project is so the thread is not full of "I can't tell what this is", and
  drop any language that sounds like marketing.

There is no official API for submitting. The Firebase API is read-only. Posting
requires your HN account in a browser.

Timing: weekday mornings US Eastern time is the conventional window.

### 1c. DEV — technical article

| Field | Value |
|---|---|
| Platform | DEV Community (dev.to) |
| Opportunity | Technical article on ranked fixture matching for HTTP replay |
| URL | https://dev.to/new |
| Rules checked | 2026-09-30 |
| Rules source | https://dev.to/terms (section 11), https://dev.to/p/editor_guide, https://dev.to/help/writing-editing-scheduling |
| Login required | Yes |
| Status | `drafted` — see `outreach/dev-ranking.md` |

Current rules that shape the draft:

- Terms section 11: content must be "on-topic, of high-quality, and is not
  designed primarily for the purposes of promotion or creating backlinks."
- "Posts must contain substantial content — they may not merely reference an
  external link that contains the full post." So the article has to actually
  teach the ranking algorithm, not link to the repo and move on.
- Up to four tags.
- There is a specific published guide for AI-assisted articles at
  https://dev.to/guidelines-for-ai-assisted-articles-on-dev. Read it before
  publishing. It exists precisely because disclosure is expected.
- Cross-posting from your own blog is explicitly encouraged, and RSS import is
  supported, so an article on your own site can also be posted to DEV.

The article teaches a real algorithm: how you score and rank HTTP fixture
candidates so that an exact path beats a wildcard regardless of file order, and
how the ranking tuple is built. That is genuinely interesting content, and it
happens to be an accurate description of the code.

### 1d. Reddit

Reddit rules could not be read directly: `www.reddit.com/r/*/about/rules`
returns 403 to automated requests and `old.reddit.com` now redirects to login.
Everything below comes from mirrors and search snippets, is dated, and **must
be re-checked in a logged-in browser before you post**. Reddit mods change
rules constantly.

Do not cross-post the same text to more than one subreddit. Each draft below
is written for one subreddit and only one of them.

#### r/SideProject — `drafted`

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/SideProject/ |
| Rules | No subreddit-specific rules are published on its rules page. That is not permission. Say plainly it is yours, make the post useful on its own, use the correct flair. |
| Verified | 2026-09-26 via mirror. Activity confirmed: ~400 posts/day. |
| Draft | `outreach/reddit-sideproject.md` |
| Status | `ready` once you rewrite it in your own voice |

This is the best fit of the Reddit options. The sub exists to show projects.

#### r/opensource — `drafted`

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/opensource/ |
| Rules | Encourages promoting your own work to a degree, but recommends under 10% of your posts be promotional. Flair `Promotional` is required. Repositories must carry an OSI-approved LICENSE file or the post is removed — MockRelay has MIT. If your post links an article, the title must match the article's title. No link aggregations. |
| Verified | 2026-09-26 via mirror |
| Draft | `outreach/reddit-opensource.md` |
| Status | `ready` |

#### r/webdev — `drafted`, Saturday only

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/webdev/ |
| Rules | Sharing a project or asking for feedback on it is **limited to Showoff Saturday**. Any other day it is removed. Correct flair is enforced. "No excessive self-promotion... refer to the Reddit 9:1 rule." No commercial promotion. LLM-generated low-effort posts are removed. |
| Verified | 2026-09-26 via mirror |
| Draft | `outreach/reddit-webdev.md` |
| Status | `drafted` — post on a Saturday |

#### r/devops — `manual`, weekly thread

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/devops/ |
| Rules | Self-promotion goes **in the weekly self-promotion thread**, nowhere else. Personal affiliation must be disclosed at the top of the post or comment. "Submissions must include discussion information. Can't be just a link." |
| Verified | 2026-09-26 via mirror |
| Status | `drafted` — write a comment for the next weekly self-promotion thread |

#### r/Python — showcase thread only

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/Python/ |
| Rules | Standalone showcase posts are **no longer allowed**. They must go in the monthly showcase post or a daily thread. Showcase posts must be text, not an image or link post, must carry showcase flair, must link to source code, and must contain "What My Project Does", "Target Audience", and "Comparison". |
| Verified | 2026-09-26 via mirror. **Re-check: this rule was changed during 2026.** |
| Draft | `outreach/reddit-python-showcase.md` — structured to the three required sections |
| Status | `ready` once you rewrite it |

#### r/programming — skip, or answer as an engineer

| Field | Value |
|---|---|
| URL | https://www.reddit.com/r/programming/ |
| Rules | "r/programming is not the place to post a project to get feedback, ask for help, or otherwise promote it. Technical write-ups on what makes a project technically challenging, interesting, or educational are allowed and encouraged, but just a link to a GitHub page or a list of features is not." Also: "No LLM-Written Content." |
| Status | `skip` for a launch post. Useful only later, as your own hand-written answer to someone else's question, and only if it solves their problem. |

#### Do not target

| Subreddit | Why not |
|---|---|
| r/softwaretesting | Commercial and self-promotional testing-tool links are removed. A karma gate for new accounts was added in July 2026. |
| r/ExperiencedDevs | Rule 8 is "No Surveys/Advertisements"; there is a 3+ years experience gate. |
| r/TestAutomation | Dormant. Every indexed post is from 2017-2020. |
| r/softwareguitardev | No evidence this subreddit exists. |

### 1e. Lobsters — `manual`

| Field | Value |
|---|---|
| URL | https://lobste.rs/ |
| Opportunity | Submit with the `show` tag |
| Rules checked | 2026-09-30 |
| Rules source | https://lobste.rs/about, https://lobste.rs/t/show |
| Login required | Yes |
| Status | `drafted` — see `outreach/lobsters.md` |

Relevant rules: self-posts are welcome under the `show` tag. "As a rule of
thumb, self-promo should be less than a quarter of one's stories and comments."
Don't use it "as a write-only tool for product announcements." The `show` tag is
off-limits to accounts younger than 70 days, so the account needs to exist
first. Use it for one technical story, not a launch announcement.

### 1f. GitHub Discussions — `submitted`

| Field | Value |
|---|---|
| URL | https://github.com/sswivell/mock-relay/discussions/22 |
| Category | Show and tell |
| Status | `submitted` |

Categories already existed (Announcements, General, Ideas, Q&A, Show and tell).
The repo had Discussions enabled with nothing in it, which reads as abandoned to
anyone deciding whether to contribute. The post is in
`outreach/github-discussion.md`.

### 1g. Good first issues — `submitted`

The repo had a `good first issue` label, a CONTRIBUTING.md section pointing at
it, and nothing behind it. A contributor who clicks that link and finds an empty
list concludes the project has no room for them.

| Issue | Labels |
|---|---|
| https://github.com/sswivell/mock-relay/issues/24 | `good first issue`, `tests` |
| https://github.com/sswivell/mock-relay/issues/25 | `good first issue`, `documentation` |

A third (a CI recipe for GitHub Actions) was opened as #23 and then closed,
because PR #21 already landed that work. Closing it keeps the list honest
rather than offering a contributor something that is already done.

---

## 2. Awesome lists

All three were verified against the actual repository and its current rules on
2026-09-30. One tool per PR, follow the file's existing format, follow its
contribution rules, and expect editorial review. These are not spam: two
targeted, well-formed entries in lists that demonstrably accept them.

### 2a. cleder/awesome-python-testing — `submitted`

| Field | Value |
|---|---|
| URL | https://github.com/cleder/awesome-python-testing |
| Section | `README.md` → `## Mock and Stub` |
| Format | `- [Name](url) - Description.` alphabetized within the section |
| Rules | No CONTRIBUTING.md exists; observable convention from merged PRs is one tool per PR, strict alphabetical placement, sentence-ending period. `typos` and `rumdl` lint enforced by pre-commit. Human editorial merge required; ~1-5 day turnaround. |
| Activity | 312 stars, last commit 2026-09-29, four external entries merged in the two weeks to 2026-09-23 |
| Status | `submitted` — https://github.com/cleder/awesome-python-testing/pull/129 |

This is the best topical fit: the section already contains Cornell
("record & replay mock server") and Mockintosh. Placed between `Mockintosh` and
`moto` to keep the section alphabetical.

### 2b. marmelab/awesome-rest — `submitted`

| Field | Value |
|---|---|
| URL | https://github.com/marmelab/awesome-rest |
| Section | `README.md` → `## Testing` → `### Mocking` |
| Format | `* [Name](url) - Sentence.` with `*` bullets |
| Rules | No CONTRIBUTING.md exists. The section is **not** alphabetised, so the entry was appended after `Mockae`. |
| Activity | 3,918 stars, last push 2026-09-23 |
| Status | `submitted` — https://github.com/marmelab/awesome-rest/pull/230 |

Note: the default branch on this repo is `master`, not `main`.

Expect a wait. The Mocking section currently has a backlog of unmerged PRs
(MockBase from 2026-09-09, DriftWire from 2026-09-22), so this will likely sit
for weeks. That is normal for this list, not a rejection.

### 2c. vinta/awesome-python — skip for now

| Field | Value |
|---|---|
| URL | https://github.com/vinta/awesome-python |
| Section | `## Testing` → `- Mock` |
| Status | `skip` |

The rules from its CONTRIBUTING.md make this a bad bet today:

- "max 3 obvious choices + 2 challengers per use case, hard max 5"
- "once a use case is at its cap, the only way in is to name the entry your
  project replaces"
- "admission is decided by maintainer editorial judgment, informed primarily
  by **PyPI download counts rather than GitHub stars**"
- Structure changes are maintainer-only, so an entry PR cannot create the
  subcategory it needs
- Automatic rejection for "coordinated multi-entry self-promotion"

The `- Mock` category is at cap and the incumbent is `vcrpy`. A displacement
argument is a real argument, not a stunt — but it is much stronger once
MockRelay is on PyPI with a real download count. Revisit after the PyPI
release. Do not attempt it before.

---

## 3. Directories and newsletters

Only the ones where a record/replay mock proxy genuinely belongs and where the
submission path is verifiable.

| Target | URL | Status | Notes |
|---|---|---|---|
| LibHunt | https://www.libhunt.com/r/mock-relay | **`submitted`** | No login required. Accepted and indexed at https://www.libhunt.com/repo/3893156/suggest_alternative. It already groups MockRelay with Hoverfly and similar service-virtualization tools. |
| PyCoder's Weekly | https://pycoders.com/submissions | `manual` | Google Form, no login. Explicitly accepts "projects you are working on". Last issue #754, 2026-09-29, so it is active. Submission in `outreach/newsletters.md`. |
| console.dev | https://console.dev/selection-criteria | `manual` | Email `hello@console.dev`. Requires the developer to be the primary user, actively maintained, good docs, and self-service signup. Open source is not excluded. Submission in `outreach/newsletters.md`. |
| Changelog News | https://changelog.com/news/submit | `manual` | Login required. "Submitting your own work is also encouraged." Explicitly rejects commercial products, so an open source tool is fine. Submission in `outreach/newsletters.md`. |
| Python Weekly | https://www.pythonweekly.com/ | `skip` | Active (issue #764, 2026-09-24) but the site migrated to beehiiv and `/submit` returns 404. Submission path **UNVERIFIED**. Email route not confirmed. Investigate by hand. |
| OpenAlternative | https://openalternative.co/submit | `skip` | Every entry is framed as "Open Source Alternative to X", a proprietary product. A record/replay mock proxy has no clean proprietary analogue, and inventing one would be dishonest framing. |
| libraries.io | — | n/a | Not a submission target. It scrapes PyPI automatically. Publishing to PyPI is the action that matters. |
| Product Hunt | https://www.producthunt.com | `skip` | It is a launch-marketing channel, not developer discovery for a testing tool. Off-strategy. |

### Verified as dead, irrelevant, or unusable

| Target | Why skipped |
|---|---|
| sindresorhus/awesome | Structurally cannot list a tool, only other lists. Its PR template requires adding *a list*, and explicitly states "Fully AI-generated pull requests are not accepted". |
| atinfo/awesome-test-automation | Dormant; last push 2025-11-28. |
| elangosundar/awesome-api-tools | Last push 2022-11-06. |
| savkat/awesome-api | 0 stars, 0 forks, 0 commits. Non-functional. |
| InfoQ recommendations | `https://www.infoq.com/recommendations/` is a verified 404. Editorial only. |
| awesomeopensource.com | No submission form could be verified. Third-party sites claim one exists; do not trust it. |
| open-source.post, gitstar-ranking.com, newsletter.town | Unreachable at the time of checking. Check by hand if you care. |
| TLDR, Bytes, APIs You Won't Hate, Awesome Newsletter, Explore.dev, This Week in Python | No public submission form found. TLDR and Bytes are editorially curated with no submission affordance; the rest were unreachable. |

A useful side note: the GitHub topic `record-replay` is real and sparse. Topics
are self-applied, so MockRelay has been tagged with it along with the other
relevant ones.

---

## 4. Answering existing questions

The best version of this is not a launch post. It is being the person who
already answered the question. Search for open threads along these lines and
answer them with `outreach/answer-template.md`, adapted to what was actually
asked:

- "How do I mock a third-party API in tests?"
- "How do I record HTTP traffic for use in tests?"
- "How do you test against an API without hitting the real one?"
- "How do I replay API responses offline?"
- "How do you create deterministic API fixtures?"
- "How do you avoid burning a third-party rate limit in CI?"
- "vcrpy vs hand-written mocks for integration tests"
- "mitmproxy or WireMock for local API development"

Rules for this one, which matter more than the rules for a launch post:

1. Answer the question first and completely. The tool is at most a paragraph of
   it.
2. If MockRelay genuinely does not fit their situation, say so and suggest what
   does. `outreach/answer-template.md` has a version of this.
3. Never paste the same reply into multiple threads.
4. Disclose that you wrote it, immediately, and do not hide it.
5. Do not reply to a thread unless the answer is actually useful to someone
   reading it later. Comment volume is not the goal.

Do not go looking for threads to insert the name into. That is astroturfing
with extra steps, and it is exactly the behaviour that gets a project
blacklisted from developer communities.

---

## 5. Post drafts

| File | Angle | For |
|---|---|---|
| `outreach/show-hn.md` | Engineering, record/replay | Hacker News `Show HN` |
| `outreach/dev-ranking.md` | Teaching, ranked matching | DEV |
| `outreach/reddit-sideproject.md` | Show and tell | r/SideProject |
| `outreach/reddit-opensource.md` | Open source | r/opensource |
| `outreach/reddit-webdev.md` | Showoff Saturday | r/webdev |
| `outreach/reddit-python-showcase.md` | Structured showcase | r/Python monthly thread |
| `outreach/reddit-devops.md` | Weekly self-promo comment | r/devops |
| `outreach/lobsters.md` | Technical story | Lobsters `show` |
| `outreach/github-discussion.md` | Feedback request | GitHub Discussions |
| `outreach/newsletters.md` | Short submissions | PyCoder's Weekly, console.dev, Changelog |
| `outreach/awesome-list-prs.md` | Directory entries | awesome-python-testing, awesome-rest |
| `outreach/answer-template.md` | Helping someone | Any forum, Slack, or thread |
| `outreach/good-first-issues.md` | Contributor onboarding | GitHub issues |

---

## 6. Repository changes made for discoverability

These were done in-repo because a broken or unclear front door was the real
bottleneck.

| Change | Why |
|---|---|
| README rewritten around the problem, the audience, and an explicit "when this is the wrong tool" section | A developer searching "API mocking" or "record HTTP traffic for tests" should understand the fit, and the non-fit, in under 30 seconds |
| README: Docker install path | Some developers will not or cannot `pip install` |
| README: CI recipe | CI is the stated use case and had no copy-pasteable snippet |
| README: comparison table against vcrpy, responses/respx, WireMock, Prism, Hoverfly, mitmproxy | Answers the question people actually ask, without claiming to be better than everything |
| `Dockerfile` and `.dockerignore` | Referenced in the README; ROADMAP already tracked it under `ci` |
| `.github/workflows/publish.yml` | PyPI trusted publishing, gated on the full test matrix and ruff |
| `pyproject.toml`: more keywords, mock/testing classifiers, `Source`/`Discussions`/`Funding` URLs, Dockerfile in the sdist | Package metadata is indexed by search and by libraries.io |
| GitHub topics expanded to 20 | Topics are self-applied and free, and they are how people find projects in the first place |
| GitHub Discussions welcome post and three `good first issue` issues | A repo with an empty tracker looks abandoned to a prospective contributor |

---

## 7. What is deliberately not claimed

Not because these are false, but because nothing in this repository verifies
them. If you add any of them, add the number and where it came from.

- No stars, forks, watchers, or contributor counts are quoted anywhere.
- No download counts, because MockRelay is not on PyPI.
- No user or company count.
- No testimonials or quotes from anyone.
- No benchmark numbers comparing MockRelay to another tool.
- No "trusted by" or "used in production at" claims.
- No "stars welcome" or "please upvote" anywhere. Both are the kind of request
  that turns a sympathetic reader off.