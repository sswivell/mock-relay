"""Demonstration of ranked smart matching and match_priority."""
from __future__ import annotations

from mockrelay._06 import _01 as MatchSpec
from mockrelay._06 import _04 as Request
from mockrelay._06 import _05 as Response
from mockrelay._06 import _06 as Fixture
from mockrelay._09 import _07 as MatchOptions
from mockrelay._09 import _22 as match_fixtures


def _01(name: str) -> None:
    print(f"\n--- {name} ---")


def _02(rows: list[dict]) -> None:
    for idx, r in enumerate(rows, start=1):
        hit = "HIT " if r["matched"] else "MISS"
        print(
            f"  {idx}. [{hit}] {r['id']:<20} "
            f"strategy={r['strategy']:<8} score={r['score']:<4} status={r['status']}"
        )


def main() -> None:
    print("MockRelay Smart Matching Showcase")

    f1 = Fixture(
        id="users-wildcard",
        upstream="demo",
        match=MatchSpec(method="GET", path="wildcard:/users/*"),
        request=Request(method="GET", path="/users/*"),
        response=Response(status=200, body={"tier": "generic_user"}),
    )
    f2 = Fixture(
        id="users-specific-42",
        upstream="demo",
        match=MatchSpec(method="GET", path="/users/42"),
        request=Request(method="GET", path="/users/42"),
        response=Response(status=200, body={"tier": "vip_user", "id": 42}),
    )
    f3 = Fixture(
        id="orders-filter-gt100",
        upstream="demo",
        match=MatchSpec(
            method="POST",
            path="/orders",
            body_contains={"status": "paid", "total": {"$gt": 100}},
        ),
        request=Request(method="POST", path="/orders"),
        response=Response(status=201, body={"discount": "premium"}),
    )

    fixtures = [f1, f2, f3]

    _01("1. Specificity ranking: exact path wins over wildcard")
    print("Request: GET /users/42")
    res1 = match_fixtures(fixtures, "GET", "/users/42", {}, None)
    _02(res1)
    print(f"Winner: {res1[0]['id']} (exact match ranked higher than wildcard)")

    _01("2. Fallback to wildcard when no exact fixture exists")
    print("Request: GET /users/99")
    res2 = match_fixtures(fixtures, "GET", "/users/99", {}, None)
    _02(res2)
    print(f"Winner: {res2[0]['id']}")

    _01("3. Body operator matching ($gt: 100)")
    print("Request: POST /orders with body {'status': 'paid', 'total': 250}")
    res3 = match_fixtures(
        fixtures, "POST", "/orders", {}, {"status": "paid", "total": 250}
    )
    _02(res3)
    print(f"Winner: {res3[0]['id']}")

    _01("4. Match priority reordering (query outranking path)")
    f_path_exact = Fixture(
        id="fx-exact-path",
        upstream="demo",
        match=MatchSpec(method="GET", path="/items/item_1"),
        request=Request(method="GET", path="/items/item_1"),
        response=Response(status=200, body={"label": "exact path match"}),
    )
    f_query_exact = Fixture(
        id="fx-wildcard-query",
        upstream="demo",
        match=MatchSpec(
            method="GET",
            path="wildcard:/items/*",
            query_subset={"preview": ["true"]},
        ),
        request=Request(method="GET", path="/items/*"),
        response=Response(status=200, body={"label": "query preview match"}),
    )
    prio_fixtures = [f_path_exact, f_query_exact]

    default_opts = MatchOptions(order=("path", "body", "query", "literal"))
    query_first_opts = MatchOptions(order=("query", "path", "body", "literal"))

    print("Request: GET /items/item_1?preview=true")
    res_default = match_fixtures(
        prio_fixtures, "GET", "/items/item_1", {"preview": ["true"]}, None, default_opts
    )
    print("Default priority (path > body > query > literal):")
    print(f"  Winner: {res_default[0]['id']}")

    res_custom = match_fixtures(
        prio_fixtures, "GET", "/items/item_1", {"preview": ["true"]}, None, query_first_opts
    )
    print("Reordered priority (query > path > body > literal):")
    print(f"  Winner: {res_custom[0]['id']}")


if __name__ == "__main__":
    main()
