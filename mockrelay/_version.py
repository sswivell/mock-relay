"""The single source of truth for the MockRelay version.

Nothing else should hardcode a version number. `pyproject.toml` reads this
module through `[tool.hatch.version]`, and `mockrelay.__version__` re-exports
it, so `pip show mockrelay` and `mockrelay --version` cannot drift apart.
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
