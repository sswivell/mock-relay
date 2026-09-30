# Development Guide

This guide covers local environment setup, running tests, linting, building release packages, and codebase architecture conventions.

---

## Prerequisites

- Python 3.10, 3.11, 3.12, or 3.13
- Git

---

## Local Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/sswivell/mock-relay.git
   cd mock-relay
   ```

2. **Create and activate a virtual environment:**

   ```bash
   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate

   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install editable package with development dependencies:**

   ```bash
   pip install -e ".[dev]"
   ```

   Development dependencies installed from `pyproject.toml` include `pytest`, `ruff==0.16.9`, `mypy`, `build`, and `pip-audit`.

---

## Running Tests

Run the full pytest suite:

```bash
pytest -q
```

Run a specific test file or test filter:

```bash
# Run CLI tests
pytest tests/test_cli.py

# Run tests matching a keyword
pytest -k "priority"

# Run match strategy tests
pytest tests/test_match_strategies.py
```

---

## Linting and Code Quality

MockRelay pins Ruff to ensure consistent linting across local setups and CI:

```bash
ruff check .
```

To run security audit on dependencies:

```bash
pip-audit
```

---

## Packaging and Build Verification

Build the source distribution (`.tar.gz`) and binary wheel (`.whl`):

```bash
python -m build
```

Verify that the built wheel installs and runs properly:

```bash
# In a temporary environment or virtualenv:
pip install dist/mockrelay-*.whl
mockrelay --version
```

---

## Building the Documentation

The site is plain MkDocs with the theme it ships with. There is no custom CSS
and no JavaScript.

```bash
pip install -e ".[docs]"
python -m mkdocs serve          # live preview on http://127.0.0.1:8000
python -m mkdocs build --strict # writes ./site
```

`--strict` turns a broken internal link into a build failure. Run the nav check
too, which catches a page that was added to `docs/` and forgotten in the nav:

```bash
python scripts/check_docs_nav.py
```

Both run in CI before the GitHub Pages deploy.

The social preview card is committed as `docs/assets/social-preview.png`. If you
edit its SVG, regenerate the PNG:

```bash
python scripts/make_social_preview.py
```

---

## Code Architecture & Conventions

MockRelay uses a numbered internal module layout (`_01.py` through `_19.py`). This architecture is intentional and load-bearing.

| Module | Responsibility |
|---|---|
| `_01.py` | Default settings and theme constants |
| `_02.py` | Brand key encode/decode |
| `_03.py` | Color palettes and terminal capability detection |
| `_04.py` | Terminal UI rendering (tables, boxes, headers, spinners) |
| `_05.py` | `Config` loading, validation, scoped setting resolution |
| `_06.py` | Core dataclasses (`MatchSpec`, `Request`, `Response`, `Fixture`) |
| `_07.py` | Secret redaction (headers and sensitive payload patterns) |
| `_08.py` | JSON body normalization |
| `_09.py` | Smart matcher: strategies, ranked scoring, and diagnostics |
| `_10.py` | `Store`: fixture persistence, directory layout, and IDs |
| `_11.py` | `Metrics`: request counters and recent-request ring buffer |
| `_12.py` | Outbound HTTP upstream client and response decoding |
| `_13.py` | Proxy request handler and HTTP server |
| `_14.py` | Admin API server & web dashboard |
| `_15.py` | CLI entry point and argparse-based command handlers |
| `_16.py` | Demo bootstrap: settings and CLI helpers used by the examples |
| `_17.py` | Fixture counting helpers for status output |
| `_18.py` | Validation: load a config and fixture tree, describe what is wrong |
| `_19.py` | Machine-readable JSON output for the CLI |
| `errors.py` | Exception types, exit codes, and user-facing error rendering |
| `limits.py` | Resource limits (buffer, payload, and header sizes) |
| `security.py` | Filesystem, network, and header safety primitives |

The three non-numbered modules live in `mockrelay/` alongside the numbered
ones. `docs/architecture.md` carries a terse role-per-file map plus the request
and matching flow; this table is the detailed one.

### Rules for Contributions
- Python 3.10+ compatibility.
- Internal functions and classes use numbered identifiers (`_01`, `_02`, ...).
- Keep code clean and self-explanatory; no inline commentary unless strictly necessary.
- Every module must maintain a descriptive docstring at the top of the file.
- Changes to user-facing CLI behavior must be reflected in `docs/cli.md` and `README.md`.
