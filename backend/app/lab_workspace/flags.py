"""Abnormal flag engine — Sprint 007."""

from __future__ import annotations

import re
from typing import Any


def calculate_abnormal_flag(
    result_value: str,
    *,
    reference_range: str | None = None,
    manual_flag: str | None = None,
    critical_low: float | None = None,
    critical_high: float | None = None,
) -> tuple[str, list[str]]:
    """Return (flag, warnings). Never blocks entry."""
    warnings: list[str] = []
    if manual_flag and manual_flag.lower() not in ("", "normal", "auto"):
        return manual_flag.lower(), warnings

    numeric = _parse_numeric(result_value)
    if numeric is None:
        if not reference_range:
            warnings.append("No reference range configured; using normal flag")
        return "normal", warnings

    low, high = _parse_range(reference_range)
    if low is None and critical_low is not None:
        low = critical_low
    if high is None and critical_high is not None:
        high = critical_high

    if low is None and high is None:
        warnings.append("Reference range missing or invalid; flag set to normal")
        return "normal", warnings

    if critical_low is not None and numeric <= critical_low:
        return "critical_low", warnings
    if critical_high is not None and numeric >= critical_high:
        return "critical_high", warnings
    if low is not None and numeric < low:
        return "low", warnings
    if high is not None and numeric > high:
        return "high", warnings
    return "normal", warnings


def _parse_numeric(value: str) -> float | None:
    cleaned = re.sub(r"[^\d.\-]", "", str(value or "").strip())
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_range(reference_range: str | None) -> tuple[float | None, float | None]:
    """Parse 'a-b', '<x', '<=x', '>x', '>=x' (also ≤ ≥ and en dash)."""
    if not reference_range:
        return None, None
    ref = reference_range.strip().replace("–", "-").replace("≤", "<=").replace("≥", ">=")
    try:
        if ref.startswith("<="):
            return None, float(ref[2:].strip().split()[0])
        if ref.startswith("<"):
            return None, float(ref[1:].strip().split()[0])
        if ref.startswith(">="):
            return float(ref[2:].strip().split()[0]), None
        if ref.startswith(">"):
            return float(ref[1:].strip().split()[0]), None
    except (ValueError, IndexError):
        return None, None
    if "-" not in ref:
        return None, None
    parts = ref.split("-", 1)
    try:
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None, None
