# Outreach status

Live tracker. Every row was researched, and `submitted` / `published` only
appear after the submission actually happened and the URL was verified by
loading it.

Last updated: 2026-10-01

## Status vocabulary

| Status | Meaning |
|---|---|
| `researched` | Rules located and read. Nothing written or sent. |
| `ready` | Written, checked against the venue's rules, ready to send |
| `submitted` | Actually sent. URL recorded. |
| `published` | Verified publicly visible at the recorded URL |
| `pending` | Sent, awaiting review or moderation decision |
| `rejected` | Sent and refused. Not to be resubmitted. |
| `manual-action` | Needs an account, 2FA, CAPTCHA, or your judgement |
| `not-allowed` | Venue prohibits it. Skipped deliberately. |

---

## 1. GitHub awesome lists

One tool per PR, existing file format, alphabetical where the section is
alphabetised. All five are open and awaiting editorial review.

| Platform | Channel | Action | Status | URL | Date | Notes |
|---|---|---|---|---|---|---|
| GitHub | cleder/awesome-python-testing | PR, `## Mock and Stub` | submitted | https://github.com/cleder/awesome-python-testing/pull/129 | 2026-09-30 | Placed between `Mockintosh` and `moto`. Section is alphabetised. 312★, merges external PRs in ~1-5 days. |
| GitHub | marmelab/awesome-rest | PR, `## Testing > ### Mocking` | submitted | https://github.com/marmelab/awesome-rest/pull/230 | 2026-09-30 | Section is **not** alphabetised, so appended after `Mockae`. Base branch is `master`. Section has a visible PR backlog, so a long wait is normal. |
| GitHub | ZoranPandovski/awesome-testing-tools | PR, `## Contract Testing Tools` | submitted | https://github.com/ZoranPandovski/awesome-testing-tools/pull/160 | 2026-10-01 | Between `JsonSchema` and `Pact`. 374★, five external PRs merged 2026-09-29. PR body distinguishes from `Test-proxy-recorder` in the sibling section. |
| GitHub | mfornos/awesome-microservices | PR, `### Testing` | submitted | https://github.com/mfornos/awesome-microservices/pull/338 | 2026-10-01 | Between `Mitmproxy` and `MockServer`. 14.5k★, 180 merged PRs, recent merges are literally "Add MockServer to Testing". Strongest fit of the five. |
| GitHub | atinfo/awesome-test-automation | PR, `python-test-automation.md`, `Mocking` | submitted | https://github.com/atinfo/awesome-test-automation/pull/605 | 2026-10-01 | After `Mockintosh`, 4-space indent matching the subsection. 7.1k★, 278 merged PRs. Cadence is slower. |
| GitHub | vinta/awesome-python | `## Testing > - Mock` | not-allowed | — | — | Use case is at its hard cap (5 entries). Rule: "once a use case is at its cap, the only way in is to name the entry your project replaces." Judged on PyPI downloads. Revisit after a PyPI release. |
| GitHub | sindresorhus/awesome | — | not-allowed | — | — | Structurally cannot list a tool, only other lists. PR template rejects fully AI-generated PRs. |
| GitHub | augustogoulart/awesome-pytest | — | not-allowed | — | — | README carries an explicit anti-self-promo warning. Also wrong category: it is a pytest-plugin list. |
| GitHub | yosriady/awesome-api-devtools, Kikobeats/awesome-api | — | not-allowed | — | — | Perfect topical fit, but PR pipelines dormant for ~2 years and ~6 years respectively. |

## 2. Community contributions

Answering real open questions, each with affiliation disclosed in the first
line, each leading with the technical answer. Every one verified by loading the
comment URL.

| Platform | Channel | Action | Status | URL | Date | Notes |
|---|---|---|---|---|---|---|
| GitHub | kiwicom/pytest-recording #189 | Comment | published | https://github.com/kiwicom/pytest-recording/issues/189#issuecomment-5922682690 | 2026-10-01 | "VCR cassettes don't work with httpx custom transport". Open since 2025-12-14, 0 comments. Answer: the seam is the transport itself, so it is a design conflict, not a patchable gap. Stated the proxy trade-off honestly. |
| GitHub | kiwicom/pytest-recording #170 | Comment | published | https://github.com/kiwicom/pytest-recording/issues/170#issuecomment-5922683957 | 2026-10-01 | "Ignore Hosts like in vcrpy". Open since 2025-04-03, 0 comments. Answered the actual question first (no such option, and why), then the architectural alternative. Offered to write the PR if wanted rather than opening it unasked. |
| GitHub | mockoon/mockoon #1924 | Comment | published | https://github.com/mockoon/mockoon/issues/1924#issuecomment-5922689590 | 2026-10-01 | Sequential responses for one endpoint. Open, 0 comments. **Confirmed MockRelay's recorder has the same gap** and said so, then gave the workaround and its limits. This is the highest-value comment of the set because it tells them not to spend an afternoon. |
| GitHub | getsentry/responses #764 | Comment | published | https://github.com/getsentry/responses/issues/764#issuecomment-5922699166 | 2026-10-01 | "Indicate if a response is from the record". Maintainer had asked for scenarios. Gave working prior art (the `X-MockRelay-*` headers), argued the API shape, and raised the `record="new_episodes"` mixed-mode edge case. |
| GitHub | getsentry/responses #740 | Comment | published | https://github.com/getsentry/responses/issues/740#issuecomment-5922702923 | 2026-10-01 | Design feedback on `_recorder`. Shared the fixture-identity finding that cost real time, and did not redirect their work. |

Deliberately **not** posted to, having read them:

| Thread | Why not |
|---|---|
| `kevin1024/vcrpy` #968 | Topically perfect, closed 2026-09-07. Pivoting into a closed thread with 26 comments is bad manners. |
| `kiwicom/pytest-recording` #189 sibling `vcrpy` #1051 | A bug report about vcrpy internals. Showing up to suggest another tool is exactly what the community guidelines warn against. |
| `getsentry/responses` #777 "Bad Network Simulation" | Labelled `question`, but MockRelay replays fixed recordings and cannot fail 2 of 5 requests probabilistically. Half the ask, not enough. |
| `keploy/keploy` #4654 offline validator | Reasonable prior-art note, but the marginal value is low and it edges toward "use mine instead". Held in reserve. |
| `SpectoLabs/hoverfly` #1191 | About `CONNECT` / 407 proxy-auth. MockRelay does not act as a transparent forward proxy, so the pitch would be wrong. |
| Stack Overflow threads (79427863, 72929188, 77665913) | SO's own guidance: "If you respond only to questions where the answer can be something you're selling, they'll assume you're just here to sell." Answering three at once from a 0-star repo is that pattern. Revisit once there is traction. Also their AI-content policy page needs checking before any answer is written. |
| SO 40960113, 69256138, 71036183, 79520603 | 2011-2021, all already answered. Not live opportunities. |
| `mitmproxy` Discourse #942 | 2018, answered by mitmproxy staff. Best articulation of the use case anywhere, but dead. |

## 3. Directories and forms

| Platform | Channel | Action | Status | URL | Date | Notes |
|---|---|---|---|---|---|---|
| LibHunt | Directory | Form submit | submitted | https://www.libhunt.com/r/mock-relay | 2026-09-30 | No login. Accepted, indexed at https://www.libhunt.com/repo/3893156/suggest_alternative. Already groups MockRelay with Hoverfly and similar service-virtualization tools. Do not resubmit. |
| awesomeopensource.com | Directory | — | not-allowed | — | 2026-10-01 | **Same data as LibHunt** — verified: `awesomeopensource.com/project/kevin1024/vcrpy` resolves to a LibHunt project page. Submitting again would be a duplicate. |
| devsuite.co | Directory | `Testing` / `API` | manual-action | https://devsuite.co/submit | — | Best-fit directory of the set: standalone dev tools, no "must be an alternative to X" constraint. `/submit` 302s to login. Passwordless magic link or OAuth. Editorial approval. Rejects `vercel.app`/`netlify.app` — use the `sswivell.github.io` site. Free tier implied but the `/submit` page is behind auth, so **UNVERIFIED**. |
| terminaldock.co | Directory | `Testing` (19 tools) | manual-action | https://terminaldock.co/submit | — | Directory of terminal-based dev tools, so the audience is unusually well-matched for a CLI. Magic-link login, editorial review. Same operator as devsuite.co. |
| openalternative.co | Directory | — | manual-action | https://openalternative.co/submit | — | Active, but every listing renders "Open Source Alternative to: X", a proprietary product. A record/replay mock proxy has no clean proprietary analogue and inventing one would be dishonest framing. Lowest priority of the three. |
| ecosyste.ms | Registry | — | not-allowed | — | 2026-10-01 | Repositories API returns **HTTP 402 Payment Required**. Paywalled. No free submission path. |
| libraries.io | Registry | — | n/a | — | — | Not a submission target. Scrapes PyPI automatically. Publishing to PyPI is the action. |
| madewithopen.com, openprojects.dev, newsletter.town, open-source.post, opensourcealternative.co | Directory | — | not-allowed | — | 2026-10-01 | All five confirmed **DNS NXDOMAIN**. Dead. |
| gitstar-ranking.com, theroundup.com | Directory | — | not-allowed | — | 2026-10-01 | Star-ranking chart with no submission path, and a parked domain respectively. |
| slashdev.io | Directory | — | not-allowed | — | 2026-10-01 | Pivoted to an AI-agent software agency. No submissions. |
| Product Hunt | Launch | — | manual-action | https://help.producthunt.com/en/articles/479557-how-to-post-a-product | — | Requires a personal account (company accounts cannot post), 2+ gallery images at 1270x760, a 240x240 thumbnail, and launches go live 12:01 AM PST. It is a launch event needing social amplification, not durable discovery. Deferred until there is traction. |

## 4. Project's own repository

| Platform | Channel | Action | Status | URL | Date | Notes |
|---|---|---|---|---|---|---|
| GitHub | Discussion, Show and tell | Feedback request | published | https://github.com/sswivell/mock-relay/discussions/22 | 2026-09-30 | Repo had Discussions enabled and empty. Discloses real state (v1.0.0, no PyPI, git-URL install) and asks five questions, one of which is "where is this the wrong tool". |
| GitHub | Issue | good first issue, tests | pending | https://github.com/sswivell/mock-relay/issues/24 | 2026-09-30 | Redaction coverage for nested and array-shaped secrets. |
| GitHub | Issue | good first issue, documentation | pending | https://github.com/sswivell/mock-relay/issues/25 | 2026-09-30 | Fixture schema from a real recording rather than a hand-written example. |
| GitHub | Issue | good first issue, documentation | rejected (self) | https://github.com/sswivell/mock-relay/issues/23 | 2026-09-30 | Opened, then **closed**: PR #21 landed that work first. Not a moderation rejection. |
| GitHub | PR #21 | Discoverability work | submitted | https://github.com/sswivell/mock-relay/pull/21 | 2026-09-30 | **Merged** 2026-10-01 as `8ff2e40`, squash. All 8 checks green. |
| GitHub | Repo metadata | Description + topics | published | https://github.com/sswivell/mock-relay | 2026-09-30 | Description rewritten. Topics 11 → 14: added `http-mocking`, `api-testing`, `integration-testing`, `http-proxy`, `record-replay`, `deterministic-testing`, `testing-tools`, `python`. |

## 5. Venues requiring an account

Every one of these is blocked on credentials, not on research. All research and
copy is done. See section 7 for the exact manual steps.

| Platform | Channel | Action | Status | URL | Date | Notes |
|---|---|---|---|---|---|---|
| Hacker News | Show HN | Submit | manual-action | https://news.ycombinator.com/submit | — | Login required. **Additionally blocked by rules, not just auth**: guidelines say "Don't post generated text or AI-edited text." Draft is in `show-hn.md` as raw material to be rewritten by hand. |
| DEV | Article | Publish | manual-action | https://dev.to/new | — | Login required. Article drafted in `dev-ranking.md`. Read https://dev.to/guidelines-for-ai-assisted-articles-on-dev before publishing. |
| Lobsters | `show` tag | Submit | manual-action | https://lobste.rs/ | — | Login required. `show` is off-limits to accounts under 70 days, so the account must already exist and be established. |
| Reddit | r/SideProject | Post | manual-action | https://www.reddit.com/r/SideProject/ | — | Login required, and Reddit returns 403 to all automated reads. Draft in `reddit.md`. |
| Reddit | r/opensource | Post, `Promotional` flair | manual-action | https://www.reddit.com/r/opensource/ | — | Same. Needs OSI LICENSE (MockRelay has MIT, so satisfied) and flair. |
| Reddit | r/webdev | Post on Showoff Saturday | manual-action | https://www.reddit.com/r/webdev/ | — | Same. **Saturday only.** |
| Reddit | r/devops | Weekly self-promo thread comment | manual-action | https://www.reddit.com/r/devops/ | — | Same. Weekly thread only, affiliation disclosed at top. |
| Reddit | r/Python | Monthly showcase thread comment | manual-action | https://www.reddit.com/r/Python/ | — | Same. **Standalone showcases are banned as of 2026.** Needs the three required sections. |
| Reddit | r/programming | — | not-allowed | — | — | "not the place to post a project to get feedback, ask for help, or otherwise promote it." Also has an explicit no-LLM-content rule. |
| Reddit | r/softwaretesting | — | not-allowed | — | — | Commercial/self-promotional tool links removed; karma gate added July 2026. |
| Reddit | r/ExperiencedDevs | — | not-allowed | — | — | "No Surveys/Advertisements", plus a 3+ years experience gate. |
| PyCoder's Weekly | Newsletter | Form | manual-action | https://pycoders.com/submissions | — | Google Form, **no login**. Copy in `newsletters.md`. Active (issue #754, 2026-09-29). |
| console.dev | Newsletter | Email | manual-action | https://console.dev/selection-criteria | — | `hello@console.dev`. Copy in `newsletters.md`. Meets their criteria. |
| Changelog News | Newsletter | Submit | manual-action | https://changelog.com/news/submit | — | Login required. "Submitting your own work is also encouraged." Copy in `newsletters.md`. |
| Python Weekly | Newsletter | — | not-allowed | — | — | Active but migrated to beehiiv; `/submit` is a 404. No submission path found. |
| Discord / Slack | Showcases | — | manual-action | — | — | No single authoritative community. Each has its own rules and most relevant ones (OpenAPI, Python, testing) gate their showcase channels. Needs account creation, which is a human action. |

## 6. Results

Measured, not predicted. Baseline before this work started: **0 stars, 4 forks,
0 watchers, 0 issues, 0 discussions**.

| Metric | Baseline | Current | Delta |
|---|---|---|---|
| Stars | 0 | 0 | 0 |
| Forks | 0 | 4 | +4 (pre-existing, unchanged by this work) |
| Watchers | 0 | 0 | 0 |
| Open issues | 0 | 2 | +2 |
| Discussions | 0 | 1 | +1 |
| Pull requests (own repo) | 1 | 2 | +1 (PR #21, merged) |
| External PRs opened | 0 | 5 | +5 |
| Technical comments on third-party issues | 0 | 5 | +5 |
| Directories indexed | 0 | 1 | +1 |
| PyPI downloads | n/a | n/a | not published |

**Stars and watchers are unchanged, and that is the honest result.** Directory
and awesome-list listings are crawled and indexed rather than generating
immediate traffic, third-party issue comments convert at the maintainer
relationship level rather than the visitor level, and the whole effort so far
has been front-door work whose effect shows up over weeks rather than hours.

No metric here was influenced by anything other than publishing things people
asked for. Nothing was bought, voted, faked, or astroturfed.

## 7. Manual actions

Ordered by expected impact.

### 1. PyPI — blocks the most downstream value

**Site:** PyPI
**Action:** Create the project, configure trusted publishing, publish
**URL:** https://pypi.org/manage/account/project/

The workflow exists and is tested. `mockrelay` was verified available
(`https://pypi.org/pypi/mockrelay/json` returns 404, i.e. no project).

1. Create the project named `mockrelay`.
2. Create a GitHub environment named `pypi` on the repository
   (Settings → Environments).
3. On PyPI, add a pending publisher: repository `sswivell/mock-relay`, workflow
   `publish.yml`, environment `pypi`.
4. Publish a GitHub release. The `pypi` job runs on release publication, gated
   behind the full test matrix and ruff.
5. After it lands, flip the install block in `README.md`, `docs/index.md`, and
   `docs/getting-started.md` to `pip install mockrelay` and delete the "not on
   PyPI yet" notes. Those notes are still in place because claiming a PyPI
   release that does not exist would be a lie in the project's own README.

**Why first:** the current install is `pip install "mockrelay @ git+https://..."`.
That requires git, builds from source, and reads as "hobby repo, be careful".
It also gates `vinta/awesome-python`, which ranks candidates by PyPI download
count, and libraries.io, which only indexes PyPI.

### 2. Hacker News — Show HN

**Site:** news.ycombinator.com
**Action:** Rewrite and submit
**URL:** https://news.ycombinator.com/submit
**What you need to do:** sign in, then write the post yourself.

`outreach/show-hn.md` has the accurate technical content and the structure.
Rewrite it in your own words before submitting — HN's guidelines say "Don't
post generated text or AI-edited text", and that is a rule of the venue, not a
formality. Weekday mornings US Eastern is the conventional window.

### 3. Reddit — five subreddits

**Site:** reddit.com
**Action:** Post, one subreddit at a time
**What you need to do:** sign in, re-check each `/about/rules` page, post.

Reddit's rules pages return 403 to automated reads and `old.reddit.com`
redirects to login, so the rules in `outreach/reddit.md` came from mirrors dated
2026-09-20 to 2026-09-26 and **must be re-verified in a logged-in browser**.

| Subreddit | When | Notes |
|---|---|---|
| r/SideProject | Any | Best fit. Say plainly it is yours. |
| r/opensource | Any | `Promotional` flair required. MIT satisfies the LICENSE rule. |
| r/webdev | **Saturday only** | Showoff Saturday. Correct flair enforced. |
| r/devops | Weekly thread | Self-promo thread only, not a new post. |
| r/Python | Monthly showcase thread | Standalone showcases banned. Three required sections. |

One draft per subreddit. Do not cross-post identical text.

### 4. DEV — technical article

**Site:** dev.to
**Action:** Publish
**URL:** https://dev.to/new
**What you need to do:** sign in, publish `outreach/dev-ranking.md`.

Read https://dev.to/guidelines-for-ai-assisted-articles-on-dev first. Their
Terms §11 require the post to contain the substance rather than link to it,
which is why the draft is the ranking algorithm with real output, not a project
announcement.

### 5. Newsletters and directories

| Target | URL | What you need to do |
|---|---|---|
| PyCoder's Weekly | https://pycoders.com/submissions | Fill the Google Form. No login. Copy in `newsletters.md`. |
| console.dev | https://console.dev/selection-criteria | Email `hello@console.dev`. Copy in `newsletters.md`. |
| Changelog News | https://changelog.com/news/submit | Sign in, submit. Copy in `newsletters.md`. |
| devsuite.co | https://devsuite.co/submit | Magic-link login, then submit. |
| terminaldock.co | https://terminaldock.co/submit | Magic-link login, `Testing` category. |
| Lobsters | https://lobste.rs/ | Account must be 70+ days old. Submit with `show` tag. |

## 8. Standing constraints

These hold for every future action taken under this project.

- No bought stars, votes, followers, or reviews. No ranking manipulation.
- No fake accounts, testimonials, users, downloads, or adoption claims.
- No astroturfing: do not search for threads to insert the name into.
- No identical replies across forums. No mass DMs. No scraped contact details.
- No bypassing CAPTCHAs, moderation, or rate limits.
- No resubmitting anything that was rejected.
- No fabricated metrics, in the repo or in any post.
- Disclose affiliation in the first line of anything that is not the project's
  own repository.
- When a venue is wrong for the project, say so rather than posting anyway.