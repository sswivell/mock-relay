# DEV article draft: ranked fixture matching

Target: https://dev.to/new
Rules checked: 2026-09-30 against https://dev.to/terms (section 11),
https://dev.to/p/editor_guide, and
https://dev.to/help/writing-editing-scheduling

Suggested tags: `python`, `testing`, `http`, `devops`

## Why this article is legitimate

Terms section 11 requires content that is "not designed primarily for the
purposes of promotion or creating backlinks", and states: "Posts must contain
substantial content — they may not merely reference an external link that
contains the full post."

This article is the ranking algorithm. It explains the problem, the scoring
model, the tie-breaking, and the failure modes, with real output. MockRelay is
mentioned because it is where the code came from, which is the honest framing,
not as a call to action.

If you rewrite this into your own explanation, it stays legitimate. If you
strip the explanation and leave a link, it stops being legitimate.

## Disclosure requirement

https://dev.to/guidelines-for-ai-assisted-articles-on-dev exists for this.
Read it before you publish. It specifies how AI assistance must be disclosed on
DEV. Whatever route you take with this draft — hand-written, or assisted and
disclosed — the article needs to stand on its own as an explanation.

## Title options

```text
Ranking HTTP fixtures so the specific match wins, not the first one
```

```text
Building a fixture matcher that ranks instead of guessing
```

```text
Why "first matching fixture" is a bug in HTTP replay, and how to rank instead
```

## Draft

```markdown
If you have ever replayed recorded HTTP traffic in tests, you have probably hit
this: you record a broad route like `wildcard:/users/*`, you also record
`/users/42`, and now which one gets served depends on the order the filesystem
returned your files in.

That is not a theoretical problem. Directory iteration order is not guaranteed
across operating systems, across filesystems, or after a `git checkout` on a
different machine. A test suite that passes on your laptop and fails in CI, on
a path that is not even related to what you changed, is the symptom.

This post is about how to replace first-match-wins with an explicit ranking, and
how the ranking has to be structured so that reordering the criteria does not
change the reported score.

## The requirements

A matcher for HTTP replay needs to answer one question: given an incoming
request and a pile of recorded fixtures, which fixture did the developer mean?

Four constraints make this harder than string equality:

1. **Paths are not strings.** They can be exact, single-segment wildcards,
   multi-segment globs, regular expressions, or fuzzy patterns.
2. **Requests carry more than a path.** Query parameters and JSON bodies
   constrain which fixture applies.
3. **Fixtures constrain what they care about, not everything.** A recorded
   `GET /users` with no query params should match a request to
   `/users?page=2`, because it did not say anything about `page`.
4. **The developer needs to know why.** When the wrong fixture wins, they need
   a reason, not a shrug.

## Step 1: Put path strategies in specificity bands

Do not score a wildcard and an exact match on the same continuous scale and
hope the numbers come out right. Put them in ordered bands first:

| Strategy | Fixture prefix | Band |
|---|---|---|
| exact | the path itself, or `exact:` | 4 |
| wildcard | `wildcard:`, `glob:` | 3 |
| regex | `re:`, `regex:` | 2 |
| fuzzy | `fuzzy:` | 1 |

Then multiply by a fine-grained score within the band, so two wildcards can
still be told apart.

This one decision eliminates the whole class of bug. `/users/42` is exact, so it
is in band 4, and `/users/*` is in band 3. Nothing about file order matters
any more, because file order is not part of the key.

## Step 2: Score within the band

Two wildcards should not tie. Useful tie-breakers, roughly in order:

- **Body constraint count.** More constrained body fields means the fixture is
  more specific. A fixture asserting `total > 100` is more specific than one
  asserting nothing.
- **Query constraint count.** Same logic: a fixture pinning `?status=paid` is
  more specific than one that pins nothing.
- **Literal density.** The fraction of the pattern that is not a wildcard.
  `wildcard:/orders/*/items` is more specific than `wildcard:/orders/**`.

Literal density is the one people leave out and then regret. Two patterns in
the same band, same constraint counts, should still be separable, and the
amount of literal text is the honest signal.

## Step 3: Tuple, not score

This is the part that matters for maintainability.

The tempting design is to fold every criterion into one big integer score and
sort by it. It works, and then the day someone wants to reorder the criteria,
they discover the reported score is now lying.

Consider `X-MockRelay-Score: 4000009`. What does that number mean? Nothing a
human can read. And if you change the weights, the number changes, so it is
useless for comparing runs before and after a config change.

Sort by a tuple instead:

```python
priority, body_count, query_count, path_band, literal_density, tie_break
```

The `rank` tuple is what you sort by and what you display when explaining a
match. The `score` is a presentation detail you can render however you like,
and it can change freely without changing behaviour.

The practical benefit: reordering `match_priority` from
`[path, body, query, literal]` to `[query, path, body, literal]` changes what
"more specific" means, and it should be a pure permutation of the tuple's
elements. If your score is a weighted sum instead, that reordering changes the
scale of every other criterion too, and you cannot reason about it.

## Step 4: Partial matching on query and body

A recorded fixture should constrain only what it cares about, otherwise
recording is unusable in practice.

Query matching is subset matching: every key the fixture pins must be present
in the request with an equal value. Extra request parameters are ignored.

```json
{
  "match": {
    "method": "GET",
    "path": "/orders",
    "query_subset": { "status": "paid" }
  }
}
```

Body matching is more interesting, because exact equality is almost never what
you want. Operators make a fixture express a rule instead of a point:

```json
{
  "body_contains": {
    "status": "paid",
    "total": { "$gt": 100 },
    "$.items[*].sku": "wildcard:A*"
  }
}
```

The operators: `$eq`, `$ne`, `$gt`, `$gte`, `$lt`, `$lte`, `$in`, `$nin`,
`$exists`, `$regex`, `$contains`.

A plain scalar means equality. An object with operator keys means the rule. An
ambiguous case worth deciding up front: is `{"total": {"$gt": 100}}` a nested
field named `$gt`, or an operator? Decide once, document it, and be consistent.

For nested structure, JSONPath-style keys beat recursive dict walking. Keys like
`$.items[*].sku`, a wildcard key, a recursive descent `..id`, and a wildcard
value give you enough to describe real payloads without inventing a query
language.

## Step 5: Make the miss explain itself

A miss that says "no fixture matched" is a bad miss. What the person needs is
"these were close, and here is the check that failed."

Ranked output for a real query should show every candidate, why it won or lost,
and the specific check that decided it:

```text
  hit  prio  strategy  score    status  id                    path
  ────────────────────────────────────────────────────────────────────────
  yes  0     exact     4000009  200     shop-exact-order-101  /orders/101 [exact] vs /orders/101
  yes  0     wildcard  3000008  200     shop-wildcard-orders  wildcard:/orders/* [wildcard] vs /orders/101
  no   0     miss      0        201     shop-post-order       /orders [exact] vs /orders/101
```

Method, path, query, and body each get their own line saying pass or fail. This
is the feature that determines whether people can use the tool or give up on
it, and it is the cheapest thing to build.

## Step 6: Fuzzy is a last resort, with an escape hatch

Fuzzy path matching should never win over anything that matched structurally. It
belongs in its own band below regex.

Similarity should be the ratio of the shorter path's length to the longer's,
not an edit distance. An edit distance lets a long shared prefix score highly,
so `/users` and `/usersx` look almost identical when they are not related.

And make the threshold per-fixture where you can. A global threshold is a
compromise that is wrong for both short and long paths.

## What to redact, and when

Two rules that are easy to get wrong if you record before you think:

- **Redact responses too, not only requests.** A token comes back in a response
  body all the time. Redacting only the request side and then committing
  fixtures is a credential leak with extra steps.
- **Build the match spec from the redacted body.** Otherwise a secret can leak
  through a `body_contains` constraint, which is exactly the case nobody
  remembers to check.

## How to check the ranking is right

Two things worth having:

1. A CLI that ranks fixtures for a hypothetical request, with no server and no
   network. Useful during development and as a debugging tool later.
2. A `validate` command that loads every fixture and reports the broken ones,
   exiting non-zero so CI can gate on it. A hand-edited fixture with the wrong
   shape should fail loudly at validation time, not as an unexplained miss in
   the middle of a test run.

## Summary

- Band the path strategies. It is the single change that removes
  filesystem-order dependence.
- Tie-break within a band on constraint counts, then literal density.
- Sort by a tuple, not a weighted sum, so criteria stay reorderable.
- Match query and body as subsets and rules, not as exact equality.
- Explain every miss per-check.
- Redact both directions, and redact before building the match spec.

The code for this, if you want to read it in context, is in
[MockRelay](https://github.com/sswivell/mock-relay), Python, MIT, one
dependency. `_09.py` is the matcher. But the ideas above stand on their own and
are worth applying to whatever you are using now.
```

## After publishing

- Cross-posting is encouraged on DEV, so if you put this on your own site or a
  personal blog, link the canonical source with `canonical_url`.
- Do not repost the same article under multiple titles. That is the pattern
  that gets accounts restricted.