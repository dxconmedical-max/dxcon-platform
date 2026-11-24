"""Pure billing helpers (no Flask): price application, FIFO payment allocation and aging buckets."""

from __future__ import annotations

from datetime import date, timedelta


def parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


def clinic_unit_price(list_price: float, clinic_price: float | None, discount_pct: float) -> float:
    """A fixed clinic price wins; otherwise the catalog price minus the clinic's default discount."""
    if clinic_price is not None:
        return round(clinic_price, 2)
    pct = min(max(discount_pct or 0, 0), 100)
    return round((list_price or 0) * (1 - pct / 100), 2)


def due_date_for(period_end: date, terms_days: int) -> date:
    return period_end + timedelta(days=max(int(terms_days or 0), 0))


def allocate_payments(statements: list[dict], total_paid: float) -> list[dict]:
    """Apply payments to the oldest statements first. Adds `paid` and `outstanding` to each statement."""
    remaining = round(total_paid or 0, 2)
    out = []
    for s in sorted(statements, key=lambda x: (x["due_date"], x["period_start"])):
        applied = round(min(remaining, s["total_amount"]), 2)
        remaining = round(remaining - applied, 2)
        out.append({**s, "paid": applied, "outstanding": round(s["total_amount"] - applied, 2)})
    return out


def aging_bucket(due: date, today: date) -> str:
    late = (today - due).days
    if late <= 0:
        return "current"
    if late <= 30:
        return "d1_30"
    if late <= 60:
        return "d31_60"
    return "d60_plus"


def aging_summary(allocated: list[dict], today: date) -> dict:
    buckets = {"current": 0.0, "d1_30": 0.0, "d31_60": 0.0, "d60_plus": 0.0}
    for s in allocated:
        if s["outstanding"] <= 0:
            continue
        due = parse_date(s["due_date"])
        if due is not None:
            buckets[aging_bucket(due, today)] += s["outstanding"]
    return {k: round(v, 2) for k, v in buckets.items()}
