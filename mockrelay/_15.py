"""CLI entry point and argparse-based command handlers."""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
import time
from pathlib import Path

from ._04 import _11 as _01
from ._04 import _15 as _03
from ._04 import _16 as _04
from ._04 import _17 as _05
from ._04 import _18 as _06
from ._05 import _06 as _07
from ._09 import _22 as _31
from ._09 import _29 as _32
from ._10 import _04 as _08
from ._11 import _01 as _09
from ._12 import _06 as _13
from ._13 import _18 as _10
from ._13 import _30 as _11
from ._14 import _10 as _12
from ._17 import _02 as _17a
from ._19 import _01 as _emit
from ._version import __version__ as _01_version


def _14(cfg: _07, store) -> None:
    _01("M O C K R E L A Y", show_brand=True)
    phost, pport = _13(cfg.listen)
    ahost, aport = _13(cfg.admin_listen)
    _04("mode", cfg.mode)
    _04("latency", f"{cfg.latency_ms} ms")
    _04("proxy", f"http://{phost}:{pport}")
    _04("admin", f"http://{ahost}:{aport}")
    _04("fixtures", str(cfg.fixtures_dir.resolve()))
    counts = _17a(store)
    if counts:
        for name, n in counts.items():
            label = "fixture" if n == 1 else "fixtures"
            _04("  " + name, str(n) + " " + label)
    else:
        _04("  (empty)", "no fixtures recorded yet")
    _04("upstreams", ", ".join(cfg.upstreams.keys()) or "(none)")
    print()
    _03("upstream routes")
    rows = [[name, u.base_url, cfg._08(name)] for name, u in cfg.upstreams.items()]
    if rows:
        _05(["name", "base_url", "mode"], rows)
    else:
        _06("warn", "no upstreams defined")
    print()
    _03("try it")
    for name in cfg.upstreams:
        _06("info", f"curl http://{phost}:{pport}/{name}/...")
    _06("info", f"open  http://{ahost}:{aport}  for admin UI")
    print()


def _15(args) -> None:
    cfg = _07._07(Path(args.config))
    if args.mode:
        cfg.mode = args.mode
    if args.latency is not None:
        cfg.latency_ms = args.latency
    store = _08(cfg.fixtures_dir)
    metrics = _09()
    state = _10(cfg, store, metrics)

    _14(cfg, store)

    try:
        proxy_srv = _11(state)
    except OSError as e:
        _06("err", f"proxy bind failed: {e}")
        sys.exit(1)
    try:
        admin_srv = _12(state)
    except OSError as e:
        _06("err", f"admin bind failed: {e}")
        sys.exit(1)

    _06("ok", "serving - Ctrl-C to stop")
    print()
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print()
        _06("info", "shutting down")
        proxy_srv.shutdown()
        admin_srv.shutdown()


def _16(args) -> None:
    args.mode = "record"
    _15(args)


def _17(args) -> None:
    args.mode = "replay"
    if args.latency is None:
        args.latency = 0
    _15(args)


def _18(args) -> None:
    cfg = _07._07(Path(args.config))
    store = _08(cfg.fixtures_dir)
    rows = []
    for f in store._07(args.upstream):
        rows.append([f.upstream, f.match.method, f.match.path,
                     f.response.status, f.id])
    if getattr(args, "json", False):
        _emit(
            "list",
            {"fixtures": [
                {"upstream": up, "method": method, "path": path,
                 "status": status, "id": fid}
                for up, method, path, status, fid in rows],
             "count": len(rows)},
            problems=store.problems or None,
        )
        return
    _01("F I X T U R E S", show_brand=False)
    if not rows:
        _06("warn", "no fixtures")
        return
    _05(["upstream", "method", "path", "status", "id"], rows)


def _19(args) -> None:
    path = Path(args.path)
    if path.exists():
        _06("warn", f"refusing to overwrite {path}")
        return
    path.write_text(
        "listen: '127.0.0.1:8080'\n"
        "admin_listen: '127.0.0.1:8081'\n"
        "fixtures_dir: './fixtures'\n"
        "mode: record\n"
        "latency_ms: 0\n"
        "redact_headers: [authorization, cookie, x-api-key]\n"
        "normalize_json_paths: ['$.id', '$.created']\n"
        "match_mode: auto\n"
        "fuzzy_threshold: 0.86\n"
        "ignore_case: false\n"
        "match_priority: [path, body, query, literal]\n"
        "smart_record_paths: true\n"
        "upstreams:\n"
        "  gh:\n"
        "    base_url: 'https://api.github.com'\n"
        "    mode: record\n"
    )
    _06("ok", f"wrote {path}")


def _20(args) -> None:
    from ._01 import _09 as s
    from ._02 import _05 as b
    _01("S E T T I N G S", show_brand=False)
    for k, v in sorted(s._08().items()):
        if k == "brand_key":
            v = "***"
        _04(k, repr(v))
    print()
    _01("B R A N D", show_brand=False)
    _04("decoded", b())
    _04("key_env", "SWIVEL_BRAND_KEY")


def _22(args) -> None:
    cfg = _07._07(Path(args.config))
    store = _08(cfg.fixtures_dir)
    method = (args.method or "GET").upper()
    query: dict[str, list[str]] = {}
    for pair in args.query or []:
        k, _, v = str(pair).partition("=")
        query.setdefault(k, []).append(v)
    body: object = None
    if args.body:
        try:
            body = json.loads(args.body)
        except ValueError:
            body = args.body
    opts = _32(cfg._12(args.upstream or "", args.path))
    fixtures = list(store._07(args.upstream))
    rows = _31(fixtures, method, args.path, query, body, opts)

    if getattr(args, "json", False):
        _emit("match", {
            "method": method, "path": args.path, "query": query, "body": body,
            "upstream": args.upstream or None,
            "mode": opts.mode, "threshold": opts.threshold, "priority": opts.order,
            "candidates": rows,
            "winner": rows[0] if rows and rows[0]["matched"] else None,
            "matched": bool(rows and rows[0]["matched"]),
        })
        return

    _01("M A T C H", show_brand=False)
    _04("method", method)
    _04("path", args.path)
    _04("query", json.dumps(query, default=str) if query else "{}")
    _04("body", json.dumps(body, default=str) if body is not None else "-")
    _04("mode", f"{opts.mode} (fuzzy>={opts.threshold})")
    _04("priority", " > ".join(opts.order))
    _04("upstream", args.upstream or "(all)")
    print()
    if not rows:
        _06("warn", "no fixtures to match against")
        return
    _05(["hit", "prio", "strategy", "score", "status", "id", "path"],
        [[("yes" if r["matched"] else "no"), r["priority"], r["strategy"],
          r["score"], r["status"], r["id"], r["checks"][1]["detail"]]
         for r in rows])
    best = rows[0]
    print()
    if best["matched"]:
        _06("ok", f"winner {best['id']} via {best['strategy']} "
                  f"(score {best['score']}, status {best['status']})")
    else:
        _06("warn", "no fixture matched")
    for c in best["checks"]:
        mark = "ok" if c["ok"] else "err"
        _06(mark, f"{c['name']}: {c['detail']}")


def _23(args) -> None:
    """Check a config and the fixtures beside it, without starting anything."""
    from ._18 import _16 as _scan
    from .errors import EXIT_VALIDATION, ConfigLoadError, render_problems

    path = Path(args.config)
    as_json = getattr(args, "json", False)

    if not path.exists():
        # serve tolerates a missing config and runs on defaults; validate was
        # pointed at a file, so a missing one is the answer, not a fallback.
        from .errors import ConfigLoadError as _missing

        e = _missing(
            ["does not exist"], source=str(path),
            hint="Create one with `mockrelay init`.",
        )
        if as_json:
            _emit("validate", {"config": str(path)}, problems=e.problems)
        else:
            print(e.render())
        raise SystemExit(e.exit_code) from None

    try:
        cfg = _07._07(path)
    except ConfigLoadError as e:
        if as_json:
            _emit("validate", {"config": str(path)}, problems=e.problems)
        else:
            print(e.render())
        raise SystemExit(e.exit_code) from None

    fixture_problems, total = _scan(cfg.fixtures_dir)
    problems = [*cfg.problems, *fixture_problems]

    if as_json:
        data = {
            "config": str(path),
            "fixtures_dir": str(cfg.fixtures_dir.resolve()),
            "upstreams": len(cfg.upstreams),
            "fixtures_checked": total,
            "problems_found": len(problems),
        }
        _emit("validate", data, problems=problems)
        if problems:
            raise SystemExit(EXIT_VALIDATION)
        return

    _01("V A L I D A T E", show_brand=False)
    _04("config", str(path))
    print()

    _04("fixtures", str(cfg.fixtures_dir.resolve()))
    _04("upstreams", str(len(cfg.upstreams)))
    print()

    if not problems:
        _06("ok", "no problems found")
        return

    found = len(cfg.problems) + total
    _06("err", f"{found} problem(s) found")
    print()
    print(render_problems(
        "Validation failed",
        problems,
        hint="Fix the items above, then run `mockrelay validate` again.",
    ))
    raise SystemExit(EXIT_VALIDATION)


def _24(args) -> None:
    """Report what is recorded, grouped by upstream."""
    from ._17 import _09 as _summarise

    cfg = _07._07(Path(args.config))
    store = _08(cfg.fixtures_dir)
    rows = _summarise(store, args.upstream)
    total = sum(int(r["fixtures"]) for r in rows)
    total_bytes = sum(int(r["bytes"]) for r in rows)

    if getattr(args, "json", False):
        _emit("stats", {
            "fixtures_dir": str(cfg.fixtures_dir.resolve()),
            "upstream": args.upstream or None,
            "upstreams": rows,
            "total_fixtures": total,
            "total_bytes": total_bytes,
        }, problems=store.problems or None)
        return

    _01("S T A T S", show_brand=False)
    _04("fixtures_dir", str(cfg.fixtures_dir.resolve()))
    _04("upstream", args.upstream or "(all)")
    print()

    if not total:
        _06("warn", "no fixtures recorded yet")
        return

    _05(
        ["upstream", "fixtures", "bytes", "methods", "statuses", "oldest", "newest"],
        [[r["upstream"], r["fixtures"], r["bytes"], ",".join(r["methods"]),
          ",".join(str(s) for s in r["statuses"]),
          r["oldest"] or "-", r["newest"] or "-"]
         for r in rows])
    print()
    _04("total", f"{total} fixture(s), {total_bytes} bytes")
    for line in store._11():
        _06("warn", line)


def _25(args) -> None:
    """Remove fixtures older than a cutoff, unless this is only a preview."""
    from ._17 import _11 as _stale

    as_json = getattr(args, "json", False)
    if args.older_than <= 0:
        if as_json:
            _emit("clean", {"older_than_days": args.older_than},
                  problems=["--older-than must be a positive number of days"])
        else:
            _06("err", "--older-than must be a positive number of days")
        raise SystemExit(2)

    cfg = _07._07(Path(args.config))
    store = _08(cfg.fixtures_dir)
    picked = list(_stale(store, args.older_than, args.upstream))

    freed = 0
    for path, _fx in picked:
        with contextlib.suppress(OSError):
            freed += path.stat().st_size

    if as_json:
        removed: list[str] = []
        failures: list[str] = []
        if args.yes:
            for path, _fx in picked:
                try:
                    path.unlink()
                    removed.append(str(path))
                except OSError as e:
                    failures.append(f"{path}: {e.strerror or e}")
        _emit("clean", {
            "fixtures_dir": str(cfg.fixtures_dir.resolve()),
            "upstream": args.upstream or None,
            "older_than_days": args.older_than,
            "dry_run": not args.yes,
            "candidates": [str(p) for p, _ in picked],
            "removed": removed,
            "bytes": freed,
        }, problems=failures or store.problems or None)
        return

    _01("C L E A N", show_brand=False)
    _04("fixtures_dir", str(cfg.fixtures_dir.resolve()))
    _04("older_than", f"{args.older_than:g} day(s)")
    _04("upstream", args.upstream or "(all)")
    print()

    if not picked:
        _06("ok", "nothing to remove")
        return

    if not args.yes:
        for path, _fx in picked:
            _06("info", str(path))
        print()
        _06("warn", f"would remove {len(picked)} fixture(s), {freed} bytes")
        _06("info", "re-run with --yes to delete them")
        return

    removed = 0
    for path, _fx in picked:
        try:
            path.unlink()
            removed += 1
        except OSError as e:
            _06("err", f"{path}: {e.strerror or e}")
    _06("ok", f"removed {removed} fixture(s), freed {freed} bytes")


def _21() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mockrelay",
        description="Universal local API mock-and-record proxy",
    )
    p.add_argument(
        "--version",
        action="version",
        version=f"mockrelay {_01_version}",
        help="print the installed version and exit",
    )
    sub = p.add_subparsers(dest="cmd")

    sp = sub.add_parser("serve")
    sp.add_argument("-c", "--config", default="mockrelay.yaml")
    sp.add_argument("-m", "--mode", choices=["record", "replay", "passthrough", "hybrid"])
    sp.add_argument("-l", "--latency", type=int)
    sp.set_defaults(func=_15)

    rp = sub.add_parser("record")
    rp.add_argument("-c", "--config", default="mockrelay.yaml")
    rp.add_argument("-l", "--latency", type=int)
    rp.set_defaults(func=_16)

    rl = sub.add_parser("replay")
    rl.add_argument("-c", "--config", default="mockrelay.yaml")
    rl.add_argument("-l", "--latency", type=int)
    rl.set_defaults(func=_17)

    lp = sub.add_parser("list")
    lp.add_argument("-c", "--config", default="mockrelay.yaml")
    lp.add_argument("-u", "--upstream")
    lp.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    lp.set_defaults(func=_18)

    mt = sub.add_parser("match")
    mt.add_argument("path", nargs="?", default="/")
    mt.add_argument("-c", "--config", default="mockrelay.yaml")
    mt.add_argument("-m", "--method", default="GET")
    mt.add_argument("-u", "--upstream")
    mt.add_argument("-q", "--query", action="append")
    mt.add_argument("-b", "--body")
    mt.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    mt.set_defaults(func=_22)

    ip = sub.add_parser("init")
    ip.add_argument("path", nargs="?", default="mockrelay.yaml")
    ip.set_defaults(func=_19)

    cp = sub.add_parser("config")
    cp.set_defaults(func=_20)

    vp = sub.add_parser("validate", help="check a config and its fixtures")
    vp.add_argument("-c", "--config", default="mockrelay.yaml")
    vp.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    vp.set_defaults(func=_23)

    st = sub.add_parser("stats", help="count what has been recorded")
    st.add_argument("-c", "--config", default="mockrelay.yaml")
    st.add_argument("-u", "--upstream")
    st.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    st.set_defaults(func=_24)

    cl = sub.add_parser("clean", help="remove fixtures older than a cutoff")
    cl.add_argument("-c", "--config", default="mockrelay.yaml")
    cl.add_argument("-u", "--upstream")
    cl.add_argument("--older-than", type=float, default=30.0,
                    help="age in days; older fixtures are removed")
    cl.add_argument("--yes", action="store_true",
                    help="actually delete; without it this is a preview")
    cl.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    cl.set_defaults(func=_25)

    return p


def _40(argv: list[str] | None = None) -> None:
    for _stream in (sys.stdout, sys.stderr):
        # Not every stream is reconfigurable: pytest's capture objects, and
        # a detached stream, both raise here.
        with contextlib.suppress(AttributeError, ValueError, OSError):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        argv = ["serve"]
    parser = _21()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


