"""Fill reference range + unit from ACTIVE DxCon reference ranges (never guesses)."""
from __future__ import annotations

from datetime import date, datetime

from app.models.patient import Patient
from app.models.reference_range import ReferenceRange
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


def _unit_for(test_code: str) -> str | None:
    """Unit does not depend on age or sex: any ACTIVE row for the test is enough."""
    row = (
        ReferenceRange.query.filter(
            ReferenceRange.test_code == test_code,
            ReferenceRange.status == "ACTIVE",
            ReferenceRange.unit.isnot(None),
            ReferenceRange.unit != "",
        )
        .order_by(ReferenceRange.id.asc())
        .first()
    )
    return row.unit if row else None


def resolve_reference(test_code: str, patient_code: str | None) -> tuple[str | None, str | None] | None:
    """Return (range_text, unit); either part may be None. None when nothing is known.

    The range needs a known age. A sex-specific row is used only when the sex
    matches; otherwise only rows for ALL are accepted. The unit is filled from
    any ACTIVE row of the test.
    """
    unit = _unit_for(test_code)
    text = None
    patient = Patient.query.get(patient_code) if patient_code else None
    age = _age_years(patient.date_of_birth) if patient is not None else None
    if patient is not None and age is not None:
        sex = _sex(patient.gender)
        row = ReferenceRangeService.resolve(test_code, age=age, sex=sex)
        if row is not None and row.sex in ("ALL", sex):
            text = format_range(row.low_value, row.high_value) or None
            unit = row.unit or unit
    if text is None and unit is None:
        return None
    return text, unit
