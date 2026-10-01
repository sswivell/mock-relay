# Newsletter and roundup submissions

Submission paths verified 2026-09-30. Status is `manual` for all of them: each
needs your email, your account, or both.

All of these are short by design. A roundup editor is reading forty links and
wants to know in ten seconds why yours is interesting. Lead with the problem,
not the name.

---

## PyCoder's Weekly

URL: https://pycoders.com/submissions
Form: Google Form at https://goo.gl/forms/aue40zIzE9jzetUa2
Login: no. Approval: none stated, no guarantee of inclusion.
Activity: issue #754 on 2026-09-29, so it is running weekly.
Accepts: "projects you are working on", which is exactly this.

```text
Title: MockRelay — a local HTTP proxy that records real API traffic and replays
it offline from JSON fixtures

URL: https://github.com/sswivell/mock-relay

Description:
A local HTTP proxy for Python. Point your app at
http://localhost:8080/<upstream>/... instead of the real URL; in record mode
it forwards upstream and writes each exchange to a redacted JSON fixture, and
in replay mode it serves those files with no network calls at all.

Fixtures are matched by rank rather than first-match-wins: path specificity
(exact > wildcard > regex > fuzzy), then body and query constraint count, then
literal density. JSON bodies match with $gt/$in/$regex operators over
JSONPath-style keys. There's a `mockrelay validate` command that exits 4 on a
broken config or fixture so CI can gate on it.

Python 3.10+, PyYAML as the only runtime dependency, MIT. Not on PyPI yet —
install is a git URL.
```

---

## console.dev

URL: https://console.dev/selection-criteria
Contact: `hello@console.dev`, per their "Submit a tool" section.
Login: no. Approval: yes, editorial.
Activity: issues on Thursdays, 2026-09-24 confirmed.

Their criteria, which the project does and does not meet:

| Criterion | MockRelay |
|---|---|
| You are the primary user | Yes |
| Self-service signup, no sales call | Yes, it is a git URL |
| Fits in the dev cycle | Yes |
| Actively maintained | Newly released, v1.0.0 |
| Good docs | Yes, published site with a full reference |
| Fast | Local proxy, no network in replay |
| No security or privacy negatives | Redaction is the point |
| Open source | Not excluded |

They also say "We do not do sponsored reviews", so send it as a submission, not
as an advert.

```text
To: hello@console.dev
Subject: Tool submission: MockRelay

Hi,

I would like to submit MockRelay, a local HTTP proxy that records real API
traffic once and replays it offline from JSON fixtures.

I am the primary user. It is open source (MIT), Python 3.10+, and installs
with a single command with no signup and no account:

  pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"

The workflow is: record mode forwards your requests to the real service and
writes each exchange to fixtures/<upstream>/*.json with secrets redacted;
replay mode serves those files with no outbound network calls at all. Fixtures
are plain JSON so they diff cleanly and can be committed next to the tests.

The piece I think is most interesting to people: fixture selection is ranked
rather than first-match-wins, so a recorded /users/42 always beats a recorded
wildcard:/users/* regardless of file order on disk. Ranking is by path
specificity, then body and query constraint count, then literal density, and
match_priority reorders it when a query param identifies a resource better than
the path does.

There is also `mockrelay validate`, which checks a config and its fixtures
without starting a server and exits 4 on a problem, so CI can gate on it.

Docs: https://sswivell.github.io/mock-relay/
Source: https://github.com/sswivell/mock-relay

Happy to answer anything.

Thanks,
sswivell
```

---

## Changelog News

URL: https://changelog.com/news/submit
Login: **yes**, required. Fields: URL, Title, "What's interesting about it?"
Status: manual.

Their policy is favourable here: "Submitting other people's work is encouraged.
Submitting your own work is also encouraged." They reject how-tos and tutorials,
and reject commercial products and services, explicitly directing those to
sponsorship. An open source tool is the good case.

Do not submit the DEV article here. This wants a project or a release, and
they reject tutorials, which is what the ranking article is.

```text
URL: https://github.com/sswivell/mock-relay

Title: MockRelay 1.0

What's interesting about it?

MockRelay is a local HTTP proxy that records real API traffic once and replays
it offline from JSON fixtures, so integration tests and local development do
not depend on a third-party API's uptime or rate limit.

The part worth a look is fixture selection. Record/replay tools typically
serve the first fixture that matches, which means a broad wildcard can shadow
a specific route depending on filesystem iteration order — a failure that
reproduces on your machine and not in CI. MockRelay scores every candidate
instead: path strategies in specificity bands (exact > wildcard > regex >
fuzzy), then body and query constraint count, then literal density, sorted by
rank tuple rather than a weighted score so the criteria stay reorderable.

Request and response both go through redaction before a fixture is written, and
the match spec is built from the redacted body so a secret cannot leak through
a body constraint.

Python 3.10+, one runtime dependency, MIT. Includes `mockrelay validate`, which
exits 4 on a broken config or fixture so a CI job can gate on it.
```

---

## Python Weekly

URL: https://www.pythonweekly.com/
Status: `skip` for now.

Active (issue #764, 2026-09-24) but the site migrated to beehiiv and
`/submit` returns 404. The submission path is **UNVERIFIED**. Worth five
minutes by hand: look for a "submit" link in the footer or a contact address.
If there is one, the PyCoder's Weekly text above works unchanged.

---

## Investigated, no submission path

| Newsletter | Finding |
|---|---|
| TLDR | Daily, active. No submission form published; `/terms` has a "Your Submissions" clause but no URL. Contact `dan@tldr.tech` is the copyright agent, not a submissions address. |
| Bytes | Active (issue 525, 2026-09-29), but editorially curated. `/submit` 404s. Advertising contact is `sponsor@fireship.dev`, which is not a submission route. |
| APIs You Won't Hate | Twice monthly, active (2026-09-01). OpenAPI/API tooling focus, genuinely relevant, but no submission form published. Related OSS list: https://openapi.tools |
| Awesome Newsletter | Host unreachable at the time of checking. |
| Explore.dev | Host unreachable. |
| This Week in Python | Host unreachable. |
| Hacker Newsletter | Curates HN content only. No submission affordance. |
| Frugal Testing | Test automation focus, relevant. Contact form only. |

If any of these turns out to have a route, the PyCoder's Weekly text above is
the right length for all of them.