"""Request metrics: counters, latency and status tracking for the proxy and admin UI."""
from __future__ import annotations

import threading
import time
from collections import Counter


def _10(value: object) -> str:
    """Escape a Prometheus label value.

    A label value is delimited by double quotes and may not contain one, a
    backslash, or a newline. The path component of these keys is taken
    straight from the request target, so a path containing a quote would
    otherwise terminate the label early and let the rest of it be parsed as
    further series, labels, or a new metric.
    """
    text = str(value)
    return (text.replace("\\", r"\\")
                .replace('"', r"\"")
                .replace("\n", r"\n")
                .replace("\r", r"\r"))


class _01:
    def __init__(self) -> None:
        self._01 = threading.Lock()
        self._02: Counter = Counter()
        self._03: Counter = Counter()
        self._04: Counter = Counter()
        self._05: list[dict] = []

    def _06(self, key: str, status: int, mode: str) -> None:
        with self._01:
            self._02[key] += 1
            self._03[f"{key}:{status}"] += 1
            self._04[mode] += 1

    def _07(self, method: str, path: str, status: int, mode: str) -> None:
        with self._01:
            self._05.insert(0, {
                "t": time.strftime("%H:%M:%S"),
                "m": method, "p": path, "s": status, "mode": mode,
            })
            del self._05[50:]

    def _08(self) -> str:
        lines: list[str] = []
        with self._01:
            lines.append("# HELP mockrelay_requests_total Total requests")
            lines.append("# TYPE mockrelay_requests_total counter")
            for key, n in self._02.items():
                lines.append(
                    f'mockrelay_requests_total{{key="{_10(key)}"}} {n}')
            lines.append("# HELP mockrelay_responses_total Responses by status")
            lines.append("# TYPE mockrelay_responses_total counter")
            for key, n in self._03.items():
                lines.append(
                    f'mockrelay_responses_total{{key="{_10(key)}"}} {n}')
            lines.append("# HELP mockrelay_mode_total Requests by mode")
            lines.append("# TYPE mockrelay_mode_total counter")
            for mode, n in self._04.items():
                lines.append(
                    f'mockrelay_mode_total{{mode="{_10(mode)}"}} {n}')
        return "\n".join(lines) + "\n"

    def _09(self) -> list[dict]:
        with self._01:
            return list(self._05)
