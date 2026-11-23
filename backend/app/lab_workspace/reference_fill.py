"""Fill reference range + unit from ACTIVE DxCon reference ranges (never guesses)."""
from __future__ import annotations

from datetime import date, datetime

from app.models.patient import Patient
from app.services.interpretation_engine_service import ReferenceRangeService


def _age_years(dob: str | None) -> int | None:
    raw = (dob or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            born = datetime.strptime(raw[:10], fmt).date()
        except ValueError:
            continue
        today = date.today()
        years = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        return years if 0 <= years <= 120 else None
    return None


def _sex(gender: str | None) -> str | None:
    g = (gender or "").strip().upper()
    if g in {"M", "MALE", "NAM"}:
        return "M"
    if g in {"F", "FEMALE", "NU", "NỮ"}:
        return "F"
    return None


def format_range(low: float | None, high: float | None) -> str:
    if low is not None and high is not None:
        return f"{low:g}-{high:g}"
    if high is not None:
        return f"<{high:g}"
    if low is not None:
        return f">{low:g}"
    return ""


def resolve_reference(test_code: str, patient_code: str | None) -> tuple[str, str | None] | None:
    """Return (range_text, unit) or None when no safe match exists.

    Needs a known age. A sex-specific row is used only when the sex matches;
    otherwise only rows for ALL are accepted.
    """
    patient = Patient.query.get(patient_code) if patient_code else None
    if patient is None:
        return None
    age = _age_years(patient.date_of_birth)
    if age is None:
        return None
    sex = _sex(patient.gender)
    row = ReferenceRangeService.resolve(test_code, age=age, sex=sex)
    if row is None:
        return None
    if row.sex not in ("ALL", sex):
        return None
    text = format_range(row.low_value, row.high_value)
    if not text:
        return None
    return text, row.unit
