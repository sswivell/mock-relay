"""Secret redaction: token/header/JSON scrubbing with placeholder substitution."""

from __future__ import annotations

import re
from typing import Any

_01 = "{{SECRET}}"
_02 = re.compile(r"Bearer\s+[A-Za-z0-9._\-]+")
_03 = re.compile(r"sk_(live|test)_[A-Za-z0-9]+")
_04 = re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")
_08 = re.compile(r"\b(?:AKIA|ASIA|ABIA|ACCA)[0-9A-Z]{16}\b")
_09 = re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")
_10 = re.compile(r"\bya29\.[0-9A-Za-z_\-]{20,}\b")
_11 = re.compile(r"\bglpat-[A-Za-z0-9_\-]{16,}\b")
_12 = re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")
_13 = re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")
_14 = re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/+_=-]{20,}")
_15 = re.compile(r"\bSG\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}\b")
_16 = re.compile(r"\bnpm_[A-Za-z0-9]{30,}\b")
_17 = re.compile(r"\bdo[oprv]_[a-f0-9]{64}\b")
_18 = re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_\-]{20,}\b")
_19 = re.compile(
    r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]*?"
    r"-----END (?:[A-Z ]+ )?PRIVATE KEY-----"
)
_20 = re.compile(r"\beyJ[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{6,}(?:\.[A-Za-z0-9_-]*)?")
_21 = re.compile(r"(?i)\b(bearer|token|secret|basic)\s+([A-Za-z0-9\-._~+/]{8,}=*)")
_22 = re.compile(r"(?i)\baws_secret_access_key\b(\s*[=:]\s*)[\"']?([A-Za-z0-9/+=]{40})")
_23 = re.compile(r"(?i)\b(://)[^\s:/@]+:[^\s@/]+@")
_24 = re.compile(
    r"(?i)([?&](?:access_token|token|api_key|apikey|key|secret|password|pwd|"
    r"auth|signature|sig|client_secret|session|sessionid|auth_token|"
    r"refresh_token)=)[^&#\s\"']+"
)
_25 = re.compile(
    r"(?i)\b(password|passwd|pwd|token|access_token|refresh_token|api_key|"
    r"apikey|client_secret|secret|authorization)=([^&\s\"';]{1,})"
)

_26: tuple[tuple[re.Pattern[str], str], ...] = (
    (_02, "Bearer " + _01),
    (_03, "sk_" + _01),
    (_04, "ghp_" + _01),
    (_19, _01),
    (_20, _01),
    (_21, r"\1 " + _01),
    (_08, _01),
    (_22, r"\1" + _01),
    (_09, _01),
    (_10, _01),
    (_11, _01),
    (_12, _01),
    (_13, _01),
    (_14, _01),
    (_15, _01),
    (_16, _01),
    (_17, _01),
    (_18, _01),
    (_23, r"\1" + _01 + "@"),
    (_24, r"\1" + _01),
    (_25, r"\1=" + _01),
)


def _05(headers: dict[str, str], redact_list: list[str]) -> dict[str, str]:
    rl = {h.lower() for h in redact_list}
    return {k: (_01 if k.lower() in rl else v) for k, v in headers.items()}


def _06(text: str) -> str:
    for pattern, replacement in _26:
        text = pattern.sub(
            lambda m, r=replacement: m.group(0) if "{{" in m.group(0) else m.expand(r),
            text,
        )
    return text


def _07(value: Any) -> Any:
    if isinstance(value, str):
        return _06(value)
    if isinstance(value, dict):
        return {k: _07(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_07(v) for v in value]
    return value
