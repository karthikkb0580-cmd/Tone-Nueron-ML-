"""Content minimisation helpers: redaction and retention-friendly excerpts."""

from __future__ import annotations

import re

_EMAIL_RE = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
_PHONE_RE = re.compile(r"(?<!\d)(\+?\d[\d\s().-]{7,}\d)(?!\d)")
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{6,}(?!\d)")
_WHITESPACE_RE = re.compile(r"\s+")


def redact(text: str, max_chars: int | None = None) -> str:
    """Mask addresses and phone-like numbers; optionally truncate.

    This is best-effort minimisation, not a guarantee of anonymisation.
    """
    if not text:
        return ""
    value = _EMAIL_RE.sub(lambda match: f"{match.group(1)}***{match.group(2)}", text)
    value = _PHONE_RE.sub("[number]", value)
    value = _LONG_NUMBER_RE.sub("[number]", value)
    value = _WHITESPACE_RE.sub(" ", value).strip()
    if max_chars and len(value) > max_chars:
        value = value[: max_chars - 1].rstrip() + "…"
    return value
