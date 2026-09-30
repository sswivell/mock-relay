# Lobsters draft

Target: https://lobste.rs/
Rules verified: 2026-09-30 against https://lobste.rs/about and
https://lobste.rs/t/show
Status: drafted, manual submission. Login required.

## What the current rules say that matters here

- Self-posts are welcome. The `show` tag exists for exactly this.
- "As a rule of thumb, self-promo should be less than a quarter of one's
  stories and comments." Do not use it as "a write-only tool for product
  announcements or driving traffic to their work."
- Tags are a closed list chosen from https://lobste.rs/tags. Pick tags that
  fit; do not invent one.
- The `show` tag is off-limits to accounts younger than 70 days, so this only
  works if the account already exists and is established.
- Submitting a domain you have not submitted before requires an established
  account too.
- Spam flag covers "created without meaningful human authorship". Lobsters is
  small and the readers are sharp. Post once, write it yourself, and do not
  resubmit.

## Recommendation

Do this only if the Lobsters account already exists and you have participated.
Post the *ranking problem*, not the tool announcement. Lobsters rewards the
interesting bit and punishes the marketing bit, and the ranking problem is
genuinely interesting on its own.

Suggested tags: `python`, `testing`. Check the actual list at
https://lobste.rs/tags and use what exists.

## Draft

```text
Title: Ranked fixture matching for HTTP replay, and why first-match-wins is a bug

Body:

Recording real HTTP traffic and replaying it is a solved idea. Picking which
recorded response to serve is not, and the usual implementation is wrong in a
way that only shows up on other people's machines.

The usual rule is "first fixture that matches wins". Which means a recorded
wildcard:/users/* shadows a recorded /users/42 whenever the filesystem hands
you the wildcard first. Directory iteration order is not stable across
operating systems or filesystems, so you get a suite that passes locally and
fails in CI for reasons unrelated to your diff.

The fix is to stop scoring strategies on one continuous scale and put them in
ordered bands first: exact 4, wildcard 3, regex 2, fuzzy 1. Within a band,
tie-break on body constraint count, query constraint count, and literal
density. File order stops being part of the key entirely.

The more interesting decision is sorting by a rank tuple rather than a weighted
score. If criteria are reorderable, which they should be, a weighted sum
changes the scale of every criterion when you permute the order, and the
reported score becomes impossible to reason about. A tuple permutes cleanly.

I wrote this up properly with the failure modes and the code:
https://sswivell.github.io/mock-relay/matching/

Questions I'm genuinely unsure about:
- Is literal density the right final tie-break, or is it just convenient?
- Should fuzzy matching be allowed to win when nothing structural matched, or
  only as an explicit opt-in per fixture?
- How do you make partial body matching ergonomic without ending up with
  twenty operators nobody uses?

(Disclosure: the matching engine described above is mine, at
https://github.com/sswivell/mock-relay. MIT, Python. Posting it because the
design questions are real and I'd like them answered.)
```