"""Configuration loading, validation, and scoped setting resolution."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import ConfigLoadError, Problem

try:
    import yaml as _01
    _02 = True
except ImportError:
    _02 = False

_MODES = ("record", "replay", "passthrough", "hybrid")
_MATCH_MODES = ("auto", "exact", "wildcard", "regex", "fuzzy")
_CRITERIA = ("path", "body", "query", "literal")
_FLAGS = ("ignore_case", "fuzzy_enabled", "metrics_enabled", "sequential",
          "smart_record_paths")
_TOP_KEYS = ("listen", "admin_listen", "fixtures_dir", "mode", "latency_ms",
             "error_injection", "metrics_enabled", "sequential",
             "redact_headers", "normalize_json_paths", "match_mode",
             "fuzzy_threshold", "ignore_case", "fuzzy_enabled",
             "smart_record_paths", "match_priority", "upstreams")
_UPSTREAM_KEYS = ("base_url", "mode", "match_mode", "fuzzy_threshold",
                  "ignore_case", "match_priority", "routes")
_ROUTE_KEYS = ("mode", "match_mode", "fuzzy_threshold", "ignore_case",
               "match_priority", "latency_ms", "error_injection")


class _03:
    def __init__(self, data: dict[str, Any]):
        self.latency_ms: int | None = data.get("latency_ms")
        self.error_injection: dict[str, Any] | None = data.get("error_injection")
        self.mode: str | None = data.get("mode")
        self.match_mode: str | None = data.get("match_mode")
        self.fuzzy_threshold: float | None = data.get("fuzzy_threshold")
        self.ignore_case: bool | None = data.get("ignore_case")
        self.match_priority: Any | None = data.get("match_priority")


class _04:
    def __init__(self, name: str, data: dict[str, Any]):
        self.name = name
        self.base_url: str = data["base_url"]
        self.mode: str | None = data.get("mode")
        self.match_mode: str | None = data.get("match_mode")
        self.fuzzy_threshold: float | None = data.get("fuzzy_threshold")
        self.ignore_case: bool | None = data.get("ignore_case")
        self.match_priority: Any | None = data.get("match_priority")
        self.routes: dict[str, _03] = {
            k: _03(v) for k, v in (data.get("routes") or {}).items()
        }

    def _05(self, path: str) -> _03 | None:
        best = None
        best_len = -1
        for prefix, ov in self.routes.items():
            if path.startswith(prefix) and len(prefix) > best_len:
                best = ov
                best_len = len(prefix)
        return best


class _06:
    def __init__(self, data: dict[str, Any] | None = None):
        d = data or {}
        self.problems: list[Problem] = []
        self.listen: str = self._19("listen", d.get("listen"), "127.0.0.1:8080")
        self.admin_listen: str = self._19(
            "admin_listen", d.get("admin_listen"), "127.0.0.1:8081")
        self.fixtures_dir: Path = self._18("fixtures_dir", d.get("fixtures_dir"))
        self.mode: str = self._20("mode", d.get("mode"), "record", _MODES)
        self.latency_ms: int = self._21("latency_ms", d.get("latency_ms"), 0)
        self.error_injection: dict[str, Any] | None = self._30(
            "error_injection", d.get("error_injection"))
        self.metrics_enabled: bool = self._22(
            "metrics_enabled", d.get("metrics_enabled"), True)
        self.sequential: bool = self._22(
            "sequential", d.get("sequential"), False)
        self.redact_headers: list[str] = self._23(
            "redact_headers", d.get("redact_headers"), [
                "authorization", "cookie", "x-api-key", "stripe-secret-key",
            ])
        self.normalize_json_paths: list[str] = self._23(
            "normalize_json_paths", d.get("normalize_json_paths"), [
                "$.id", "$.created", "$.request_id",
            ])
        self.match_mode: str = self._20(
            "match_mode", d.get("match_mode"), "auto", _MATCH_MODES)
        self.fuzzy_threshold: float = self._24(
            "fuzzy_threshold", d.get("fuzzy_threshold"), 0.86)
        self.ignore_case: bool = self._22(
            "ignore_case", d.get("ignore_case"), False)
        self.fuzzy_enabled: bool = self._22(
            "fuzzy_enabled", d.get("fuzzy_enabled"), False)
        self.smart_record_paths: bool = self._22(
            "smart_record_paths", d.get("smart_record_paths"), False)
        self.match_priority: Any | None = self._25(
            "match_priority", d.get("match_priority"))
        self.upstreams: dict[str, _04] = self._25upstreams(d.get("upstreams"))
        self._14(d)
        self._31(self.fixtures_dir)

    # Validation helpers. Each returns the value to use, recording a Problem
    # when the file disagrees. Nothing here raises: a config that is wrong
    # still has to produce a Config, because `mockrelay validate` exists to
    # describe what is wrong about it.

    def _14(self, d: dict[str, Any]) -> None:
        for key in d:
            if key not in _TOP_KEYS:
                self.problems.append(Problem(
                    "is not a known setting and was ignored",
                    subject=f"{key}:",
                    expected="one of " + ", ".join(sorted(_TOP_KEYS)),
                ))

    def _18(self, name: str, value: Any) -> Path:
        if value is None:
            return Path("./fixtures")
        if isinstance(value, Path):
            return value
        if not isinstance(value, str) or not value.strip():
            self.problems.append(Problem(
                "is not a directory path", subject=f"{name}:",
                expected="a path, for example: ./fixtures"))
            return Path("./fixtures")
        return Path(value)

    def _19(self, name: str, value: Any, default: str) -> str:
        if value is None:
            return default
        if not isinstance(value, str) or ":" not in value:
            self.problems.append(Problem(
                "is not a host:port address", subject=f"{name}:",
                expected="host:8080",
            ))
            return default
        _, _, port = value.rpartition(":")
        if not port.isdigit() or not 0 < int(port) < 65536:
            self.problems.append(Problem(
                "is not a valid port number", subject=f"{name}:",
                expected="a port between 1 and 65535",
            ))
            return default
        return value

    def _20(self, name: str, value: Any, default: str,
            allowed: tuple[str, ...]) -> str:
        if value is None:
            return default
        if value not in allowed:
            self.problems.append(Problem(
                "is not a recognised mode", subject=f"{name}:",
                expected="one of " + ", ".join(allowed),
            ))
            return default
        return str(value)

    def _21(self, name: str, value: Any, default: int) -> int:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, str)):
            self.problems.append(Problem(
                "is not a whole number of milliseconds", subject=f"{name}:",
                expected="a non-negative integer",
            ))
            return default
        try:
            n = int(value)
        except ValueError:
            self.problems.append(Problem(
                "is not a whole number of milliseconds", subject=f"{name}:",
                expected="a non-negative integer",
            ))
            return default
        if n < 0:
            self.problems.append(Problem(
                "is negative", subject=f"{name}:", expected="a value of 0 or more"))
            return default
        return n

    def _22(self, name: str, value: Any, default: bool) -> bool:
        if value is None:
            return default
        if not isinstance(value, bool):
            self.problems.append(Problem(
                "is not true or false", subject=f"{name}:",
                expected="true or false",
            ))
            return default
        return value

    def _23(self, name: str, value: Any, default: list[str]) -> list[str]:
        if value is None:
            return list(default)
        if isinstance(value, str) or not isinstance(value, (list, tuple)):
            self.problems.append(Problem(
                "is not a list of header names", subject=f"{name}:",
                expected="a list, for example: [" + ", ".join(default[:2]) + "]",
            ))
            return list(default)
        bad = [v for v in value if not isinstance(v, str)]
        if bad:
            self.problems.append(Problem(
                f"has non-text entries: {bad[0]!r}", subject=f"{name}:",
                expected="a list of header names",
            ))
            return [v for v in value if isinstance(v, str)]
        return list(value)

    def _24(self, name: str, value: Any, default: float) -> float:
        if value is None:
            return default
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            self.problems.append(Problem(
                "is not a number", subject=f"{name}:",
                expected="a number between 0.0 and 1.0",
            ))
            return default
        try:
            n = float(value)
        except ValueError:
            self.problems.append(Problem(
                "is not a number", subject=f"{name}:",
                expected="a number between 0.0 and 1.0",
            ))
            return default
        if not 0.0 <= n <= 1.0:
            self.problems.append(Problem(
                "is outside the range a similarity score can take",
                subject=f"{name}:", expected="a number between 0.0 and 1.0"))
            return default
        return n

    def _25(self, name: str, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str) or not isinstance(value, (list, tuple)):
            self.problems.append(Problem(
                "is not a list of criteria", subject=f"{name}:",
                expected="a list drawn from " + ", ".join(_CRITERIA),
            ))
            return None
        out: list[str] = []
        for v in value:
            if v not in _CRITERIA:
                self.problems.append(Problem(
                    f"is not a criterion: {v!r}", subject=f"{name}:",
                    expected="a list drawn from " + ", ".join(_CRITERIA)))
                continue
            out.append(str(v))
        return out

    def _25upstreams(self, value: Any) -> dict[str, _04]:
        if value is None:
            return {}
        if isinstance(value, (list, tuple)) or not isinstance(value, dict):
            self.problems.append(Problem(
                "is not a mapping of name to upstream settings",
                subject="upstreams:",
                expected="upstreams:\n  gh:\n    base_url: 'https://api.github.com'",
            ))
            return {}
        out: dict[str, _04] = {}
        for name, body in value.items():
            if isinstance(body, (list, str)) or not isinstance(body, dict):
                self.problems.append(Problem(
                    "is not a mapping of settings", subject=f"{name}:",
                    expected="a mapping with at least base_url"))
                continue
            self._33(name, body, _UPSTREAM_KEYS)
            for key in body:
                if key not in _UPSTREAM_KEYS:
                    self.problems.append(Problem(
                        "is not a known upstream setting and was ignored",
                        subject=f"{name}.{key}:",
                        expected="one of " + ", ".join(sorted(_UPSTREAM_KEYS))))
            if "base_url" not in body:
                self.problems.append(Problem(
                    "has no base_url", subject=f"{name}:",
                    expected="base_url: 'https://api.github.com'"))
                continue
            if not isinstance(body["base_url"], str):
                self.problems.append(Problem(
                    "is not a URL", subject=f"{name}.base_url:",
                    expected="an http:// or https:// URL"))
                continue
            self._26(name, body)
            out[name] = _04(name, body)
        return out

    def _26(self, name: str, body: dict[str, Any]) -> None:
        self._20(f"{name}.mode", body.get("mode"), "", _MODES)
        self._20(f"{name}.match_mode", body.get("match_mode"), "", _MATCH_MODES)
        self._24(f"{name}.fuzzy_threshold", body.get("fuzzy_threshold"), 0.86)
        self._22(f"{name}.ignore_case", body.get("ignore_case"), False)
        self._25(f"{name}.match_priority", body.get("match_priority"))
        self._30(f"{name}.error_injection", body.get("error_injection"))
        routes = body.get("routes")
        if routes is None:
            return
        if not isinstance(routes, dict):
            self.problems.append(Problem(
                "is not a mapping of path prefix to overrides",
                subject=f"{name}.routes:",
                expected="routes:\n  /v1/search:\n    mode: replay"))
            return
        for prefix, override in routes.items():
            if not isinstance(override, dict):
                self.problems.append(Problem(
                    "is not a mapping of overrides", subject=f"{name}.routes.{prefix}:",
                    expected="a mapping of route settings"))
                continue
            self._33(f"{name}.routes.{prefix}", override, _ROUTE_KEYS)

    def _30(self, name: str, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, dict):
            self.problems.append(Problem(
                "is not a mapping", subject=f"{name}:",
                expected="status: 500\nrate: 0.1"))
            return None
        status = value.get("status")
        if status is not None and (
                isinstance(status, bool) or not isinstance(status, int)
                or not 100 <= status <= 599):
            self.problems.append(Problem(
                "is not an HTTP status", subject=f"{name}.status:",
                expected="a status between 100 and 599"))
        rate = value.get("rate")
        if rate is not None and (
                isinstance(rate, bool) or not isinstance(rate, (int, float))
                or not 0.0 <= float(rate) <= 1.0):
            self.problems.append(Problem(
                "is not a probability", subject=f"{name}.rate:",
                expected="a number between 0.0 and 1.0"))
        return value

    def _31(self, path: Path) -> None:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self.problems.append(Problem(
                f"could not be created: {e.strerror or e}",
                subject="fixtures_dir:",
                expected="a writable directory path"))

    def _33(self, name: str, body: dict[str, Any],
            allowed: tuple[str, ...]) -> None:
        for key in body:
            if key not in allowed:
                self.problems.append(Problem(
                    "is not a known setting and was ignored",
                    subject=f"{name}.{key}:",
                    expected="one of " + ", ".join(sorted(allowed))))

    @staticmethod
    def _15(exc: Exception) -> str:
        """One line describing a parse failure, with the line it happened on.

        PyYAML's message spans several paragraphs and quotes the offending
        text; the first line alone ("while parsing a flow sequence") does not
        say where to look, and the rest is the user's own file echoed back.
        """
        mark = getattr(exc, "problem_mark", None)
        problem = str(getattr(exc, "problem", "") or "").strip()
        if not problem:
            problem = str(exc).splitlines()[0] if str(exc) else type(exc).__name__
        if mark is not None:
            return f"{problem}, at line {mark.line + 1}, column {mark.column + 1}"
        return problem

    @classmethod
    def _07(cls, path: Path) -> _06:
        p = Path(path)
        if not p.exists():
            return cls()
        try:
            text = p.read_text(encoding="utf-8")
        except OSError as e:
            raise ConfigLoadError(
                f"could not be read: {e.strerror or e}", source=str(p)) from e
        try:
            data = _01.safe_load(text) if _02 else json.loads(text)
        except Exception as e:
            # yaml.YAMLError and json.JSONDecodeError are different types but
            # both mean the same thing here: this file is not parseable.
            raise ConfigLoadError(cls._15(e), source=str(p)) from e
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ConfigLoadError(
                f"is a {type(data).__name__}, not a mapping of settings",
                source=str(p),
                hint="A config file is a set of `key: value` lines.",
            )
        return cls(data)

    def _08(self, upstream: str, path: str = "") -> str:
        up = self.upstreams.get(upstream)
        if not up:
            return self.mode
        ov = up._05(path) if path else None
        if ov and ov.mode:
            return ov.mode
        if up.mode:
            return up.mode
        return self.mode

    def _09(self, upstream: str, path: str = "") -> int:
        up = self.upstreams.get(upstream)
        if up:
            ov = up._05(path) if path else None
            if ov and ov.latency_ms is not None:
                return ov.latency_ms
        return self.latency_ms

    def _10(self, upstream: str, path: str = "") -> dict[str, Any] | None:
        up = self.upstreams.get(upstream)
        if up:
            ov = up._05(path) if path else None
            if ov and ov.error_injection is not None:
                return ov.error_injection
        return self.error_injection

    def _11(self, upstream: str) -> str | None:
        up = self.upstreams.get(upstream)
        return up.base_url if up else None

    def _12(self, upstream: str, path: str = "") -> dict[str, Any]:
        out: dict[str, Any] = {
            "match_mode": self.match_mode,
            "fuzzy_threshold": self.fuzzy_threshold,
            "ignore_case": self.ignore_case,
            "fuzzy_enabled": self.fuzzy_enabled,
            "match_priority": self.match_priority,
        }
        up = self.upstreams.get(upstream)
        if up:
            self._13(out, up)
            if path:
                ov = up._05(path)
                if ov:
                    self._13(out, ov)
        return out

    def _13(self, out: dict[str, Any], src: Any) -> None:
        for k in list(out):
            v = getattr(src, k, None)
            if v is not None:
                out[k] = v
