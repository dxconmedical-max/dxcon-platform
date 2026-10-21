"""Vietnam local time (UTC+7, no DST) for report display."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

VN_TZ = timezone(timedelta(hours=7))
_LABELED_TS = re.compile(
    r"(Released: |Approved at:</strong> )(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)"
)


def format_vn_time(value) -> str:
    """Naive datetimes/strings are treated as UTC (how the app stores them)."""
    if value is None or str(value).strip() == "":
        return "—"
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(VN_TZ).strftime("%d/%m/%Y %H:%M:%S") + " (GMT+7)"


def localize_report_times(html: str) -> str:
    """Convert UTC timestamps baked into stored report HTML. Idempotent."""
    return _LABELED_TS.sub(lambda m: m.group(1) + format_vn_time(m.group(2)), html or "")
