"""Check the documentation set for stale nav entries and broken internal links.

Run by the docs workflow after `mkdocs build --strict`, which catches links
MkDocs resolves but not files that were added to docs/ and forgotten in the
nav, or a hand-written link that points at a page which does not exist.

Standard library only, and no network: external links are collected and
counted but never fetched, so this runs offline and in under a second.

    python scripts/check_docs_nav.py [docs_dir] [mkdocs_config]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import urldefrag

REPO = Path(__file__).resolve().parent.parent

# Link shapes that are not site-internal and must be skipped rather than
# resolved. `is_external` recognises the subset that is worth counting.
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "tel:")
NON_RESOLVABLE_PREFIXES = ("//", "#", "data:")

# Fenced blocks, including ```bash ... ```, and inline code spans. Anything
# inside them is sample text, not a real link.
FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
HTML_ATTR_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
MD_LINK_RE = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)>\s]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)")
REF_LINK_RE = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?([^\s>]+)>?", re.MULTILINE)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_code(text: str) -> str:
    """Blank out fenced and inline code so sample text is not parsed."""
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines(keepends=True):
        m = FENCE_RE.match(line)
        if fence is None and m:
            fence = m.group(2)[0] * 3
            out.append("\n")
            continue
        if fence is not None:
            if line.lstrip().startswith(fence):
                fence = None
            out.append("\n")
            continue
        out.append(line)
    return INLINE_CODE_RE.sub("", "".join(out))


def nav_targets(config_text: str) -> set[str]:
    """Every .md path named in the mkdocs nav block."""
    in_nav = False
    found: set[str] = set()
    for line in config_text.splitlines():
        if line.startswith("nav:"):
            in_nav = True
            continue
        if in_nav:
            if line and not line[0].isspace():
                break
            for m in re.finditer(r"([\w\-./]+\.md)\b", line):
                found.add(m.group(1))
    return found


def link_targets(text: str) -> set[str]:
    """Every link target in a page, external and internal alike.

    Classification is deliberately left to the caller: an earlier version
    filtered external URLs out here, so the caller's external-link counter
    could only ever see zero.
    """
    body = strip_code(text)
    refs = {m.group(1) for m in MD_LINK_RE.finditer(body)}
    refs |= {m.group(1) for m in REF_LINK_RE.finditer(body)}
    refs |= set(HTML_ATTR_RE.findall(body))
    return {ref.strip() for ref in refs if ref.strip()}


def resolve(ref: str, source: Path) -> Path | None:
    """Map a link as written to the file it should point at, or None if it
    cannot be resolved without knowing the deployed URL layout."""
    target, _ = urldefrag(ref)
    if not target:
        return None
    if target.startswith("/"):
        return None  # site-root absolute; MkDocs owns those.

    candidate = (source.parent / target).resolve()
    if candidate.is_file():
        return candidate

    # A link may omit the .md suffix, or aim at a directory that MkDocs will
    # turn into an index.html.
    for suffix in (".md", "/index.md", ".html", "/"):
        alt = Path(str(candidate) + suffix)
        if alt.is_file():
            return alt
    if candidate.is_dir() and (candidate / "index.md").is_file():
        return candidate / "index.md"
    return None


def main(argv: list[str]) -> int:
    docs_dir = Path(argv[1]).resolve() if len(argv) > 1 else REPO / "docs"
    config = Path(argv[2]).resolve() if len(argv) > 2 else REPO / "mkdocs.yml"

    if not docs_dir.is_dir():
        print(f"error: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    pages = sorted(
        p for p in docs_dir.rglob("*.md")
        if not any(part.startswith((".", "_")) for part in p.relative_to(docs_dir).parts)
    )
    if not pages:
        print(f"error: no markdown pages under {docs_dir}", file=sys.stderr)
        return 1

    failures: list[str] = []
    external: set[str] = set()
    checked = 0

    for page in pages:
        text = read(page)
        rel = page.relative_to(REPO).as_posix()

        for ref in sorted(link_targets(text)):
            low = ref.lower()
            if low.startswith(EXTERNAL_PREFIXES):
                external.add(ref)
                continue
            if ref.startswith(NON_RESOLVABLE_PREFIXES):
                continue
            checked += 1
            if resolve(ref, page) is None:
                failures.append(f"{rel}: link target not found -> {ref}")

    # Files that exist but are not reachable from the nav are the usual cause
    # of a page quietly falling out of the documentation.
    if config.is_file():
        nav = nav_targets(read(config))
        for page in pages:
            rel_in_docs = page.relative_to(docs_dir).as_posix()
            if rel_in_docs in nav:
                continue
            # The homepage is always the nav's first entry; accept it under
            # either of the names people use for it.
            if rel_in_docs == "index.md" and "index.md" in nav:
                continue
            if page.name == "README.md":
                continue
            failures.append(
                f"{page.relative_to(REPO).as_posix()}: not referenced in the mkdocs nav"
            )
    else:
        failures.append(f"mkdocs config not found: {config}")

    for line in failures:
        print(f"error: {line}", file=sys.stderr)

    print(
        f"checked {checked} internal link(s) across {len(pages)} page(s); "
        f"{len(external)} external link(s) recorded, not fetched"
    )
    if failures:
        print(f"docs check failed with {len(failures)} problem(s)", file=sys.stderr)
        return 1
    print("docs check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
