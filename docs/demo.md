# Demo script

A 30-second walkthrough, written to be read aloud on camera or replayed by
[VHS](https://github.com/charmbracelet/vhs). Every block of output below was
captured from a real run, not typed out by hand.

The only thing it needs is a `gh` upstream that answers. If you do not have a
GitHub token to hand, point `gh` at any URL that returns JSON — the point of the
demo is the record/replay switch, not the payload.

---

## 0. Prepare

```bash
pip install "mockrelay @ git+https://github.com/sswivell/mock-relay.git"
mkdir demo && cd demo
mockrelay init
```

---

## 1. Record mode (about 5s)

```bash
mockrelay serve --mode record
```

The banner names the listening addresses, the mode, where fixtures will be
written, and the upstreams it will route to.

---

## 2. Make a real request (about 5s)

In a second terminal:

```bash
curl -s http://localhost:8080/gh/users/octocat
```

```json
{"login": "octocat", "id": 583231, "type": "User", "created": "2011-01-25T18:44:36Z"}
```

The response came from the real upstream, unchanged. MockRelay added one header
to mark it as recorded:

```http
X-MockRelay-Match: record
```

---

## 3. Show the fixture (about 5s)

```bash
mockrelay list
```

```text
  upstream  method  path                status  id
  ─────────────────────────────────────────────────
  gh        GET     /users/octocat      200     gh-get-016c60e26e39
```

```bash
cat fixtures/gh/*.json
```

```json
{
  "id": "gh-get-016c60e26e39",
  "upstream": "gh",
  "match": {
    "method": "GET",
    "path": "/users/octocat",
    "query_subset": {}
  },
  "request": {
    "method": "GET",
    "path": "/users/octocat",
    "query": {},
    "headers": {
      "User-Agent": "curl/8.21.0",
      "Accept": "*/*",
      "Authorization": "{{SECRET}}"
    },
    "body": null
  },
  "response": {
    "status": 200,
    "headers": { "Content-Type": "application/json" },
    "body": {
      "login": "octocat",
      "id": "{{NORMALIZED}}",
      "type": "User",
      "created": "{{NORMALIZED}}"
    }
  },
  "normalize": ["$.id", "$.created"],
  "recorded_at": "2026-09-30T01:44:41Z",
  "call_index": 0
}
```

Worth pausing on: the token is `{{SECRET}}` and the volatile IDs are
`{{NORMALIZED}}`, so this file is safe to commit and the next recording of the
same request diffs cleanly against it.

---

## 4. Replay mode (about 5s)

Stop the server with Ctrl-C and start it again:

```bash
mockrelay serve --mode replay --latency 50
```

---

## 5. The same request, offline (about 5s)

```bash
curl -i http://localhost:8080/gh/users/octocat
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
X-MockRelay-Match: exact
X-MockRelay-Fixture: gh-get-016c60e26e39
X-MockRelay-Score: 4000009
```

```json
{"login": "octocat", "id": "{{NORMALIZED}}", "type": "User", "created": "{{NORMALIZED}}"}
```

Nothing left the machine. The headers name the fixture that answered and the
score it won on.

---

## 6. Show the ranking, still without a server (about 5s)

```bash
mockrelay match /users/octocat -u gh
```

```text
  hit  prio  strategy  score    status  id                   path
  ───────────────────────────────────────────────────────────────────
  yes  0     exact     4000009  200     gh-get-016c60e26e39  /users/octocat [exact] vs /users/octocat

  ✓ winner gh-get-016c60e26e39 via exact (score 4000009, status 200)
  ✓ method: GET vs GET
  ✓ path: /users/octocat [exact] vs /users/octocat
  ✓ query: {} vs {}
  ✓ body: None vs NoneType
```

With a wildcard and an exact fixture in the same upstream, the same command
shows the exact one winning, and the `rank` column explaining why:

```text
  hit  prio  strategy  score    status  id                    path
  ─────────────────────────────────────────────────────────────────────────
  yes  0     exact     4000009  200     shop-exact-order-101  /orders/101 [exact] vs /orders/101
  yes  0     wildcard  3000008  200     shop-wildcard-orders  wildcard:/orders/* [wildcard] vs /orders/101
  yes  0     regex     2000009  200     shop-regex-orders     re:^/orders/\d+$ [regex] vs /orders/101
  yes  0     fuzzy     1000009  200     shop-fuzzy-orders     fuzzy:/ordres/101 [fuzzy] vs /orders/101
  no   0     miss      0        200     shop-glob-files       wildcard:/files/** [wildcard] vs /orders/101
  no   0     miss      0        201     shop-post-order       /orders [exact] vs /orders/101
```

---

## 7. Close on validation (about 5s)

```bash
mockrelay validate
```

```text
  ✓ no problems found
```

```bash
echo $?
```

```text
0
```

A bad fixture makes it exit `4`, which is what a CI step gates on.

---

## Optional: an automated take

[VHS](https://github.com/charmbracelet/vhs) tape for the first two steps:

```text
Output demo.gif
Set FontSize 14
Set Width 1000
Set Height 560
Set TypingSpeed 40ms

Type "mockrelay serve --mode record"
Enter
Sleep 3s
Type "curl -s http://localhost:8080/gh/users/octocat"
Enter
Sleep 2s
```
