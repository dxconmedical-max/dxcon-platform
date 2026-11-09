"""Patient consent capture at reception (paper or electronic).

Stores one row per consent type in ``patient_consents`` (append-only). The latest row
per type decides the current state, so withdrawing consent keeps the full history.
The wording of the consent form is owned by the lawyer-reviewed document; this module
only records WHAT was agreed, WHEN, in WHICH version, HOW (paper/electronic) and BY WHOM.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

from app.core.audit import write_audit
from app.extensions.db import db
from app.models.patient import Patient
from app.models.patient_consent import PatientConsent

LAB_TEST = "LAB_TEST"
PARTNER_LAB = "PARTNER_LAB"
CLINIC_SHARE = "CLINIC_SHARE"
CONTACT = "CONTACT"
OVERSEAS_STORAGE = "OVERSEAS_STORAGE"

CONSENT_TYPES = frozenset({LAB_TEST, PARTNER_LAB, CLINIC_SHARE, CONTACT, OVERSEAS_STORAGE})
REQUIRED_CONSENT = LAB_TEST
METHODS = frozenset({"PAPER", "ELECTRONIC"})
DEFAULT_VERSION = "draft-2026-11"  # column is VARCHAR(20); set the real version once the lawyer signs off


class ConsentError(ValueError):
    pass


def consent_gate_enabled() -> bool:
    """When on, orders cannot be created for a patient without a granted LAB_TEST consent."""
    return os.environ.get("CONSENT_REQUIRED_FOR_ORDERS", "").strip().lower() in {"1", "true", "yes", "on"}


def _patient(patient_code: str) -> Patient:
    code = (patient_code or "").strip()
    patient = Patient.query.filter_by(patient_code=code).first() if code else None
    if patient is None:
        raise ConsentError("Patient not found")
    return patient


def _latest_by_type(patient_code: str) -> dict:
    rows = (
        PatientConsent.query.filter_by(patient_id=patient_code)
        .order_by(PatientConsent.created_at.desc())
        .all()
    )
    latest: dict = {}
    for row in rows:
        latest.setdefault(row.consent_type, row)
    return latest


def current_consents(patient_code: str) -> dict:
    patient = _patient(patient_code)
    latest = _latest_by_type(patient.patient_code)
    out = {}
    for ctype in sorted(CONSENT_TYPES):
        row = latest.get(ctype)
        out[ctype] = None if row is None else {
            "granted": row.status == "GRANTED",
            "status": row.status,
            "version": row.consent_version,
            "recorded_at": (row.granted_at or row.revoked_at or row.created_at).isoformat()
            if (row.granted_at or row.revoked_at or row.created_at) else None,
        }
    return {"patient_code": patient.patient_code, "required": REQUIRED_CONSENT, "consents": out}


def has_required_consent(patient_code: str) -> bool:
    row = _latest_by_type((patient_code or "").strip()).get(REQUIRED_CONSENT)
    return bool(row is not None and row.status == "GRANTED")


def record_consents(patient_code: str, payload: dict, *, actor: str | None, ip_address: str = "") -> dict:
    patient = _patient(patient_code)
    items = payload.get("consents")
    if not isinstance(items, list) or not items:
        raise ConsentError("consents must be a non-empty list")
    method = str(payload.get("method") or "").upper()
    if method not in METHODS:
        raise ConsentError("method must be PAPER or ELECTRONIC")
    document_ref = str(payload.get("document_ref") or "").strip()[:100] or None
    guardian = payload.get("guardian")
    if guardian is not None and not isinstance(guardian, dict):
        raise ConsentError("guardian must be an object")
    version = str(payload.get("consent_version") or DEFAULT_VERSION).strip()[:20]

    seen = set()
    parsed = []
    for item in items:
        if not isinstance(item, dict):
            raise ConsentError("each consent must be an object")
        ctype = str(item.get("consent_type") or "").upper()
        if ctype not in CONSENT_TYPES:
            raise ConsentError(f"Unknown consent_type: {ctype or '(empty)'}")
        if ctype in seen:
            raise ConsentError(f"Duplicate consent_type: {ctype}")
        seen.add(ctype)
        granted = item.get("granted")
        if not isinstance(granted, bool):
            raise ConsentError(f"granted must be true or false for {ctype}")
        parsed.append((ctype, granted))

    now = datetime.utcnow()
    meta = {"method": method, "document_ref": document_ref, "recorded_by": actor}
    if guardian:
        meta["guardian"] = {
            "name": str(guardian.get("name") or "")[:200],
            "relationship": str(guardian.get("relationship") or "")[:100],
            "document": str(guardian.get("document") or "")[:200],
        }
    for ctype, granted in parsed:
        db.session.add(PatientConsent(
            patient_id=patient.patient_code,
            consent_type=ctype,
            consent_version=version,
            status="GRANTED" if granted else "REVOKED",
            granted_at=now if granted else None,
            revoked_at=None if granted else now,
            ip_address=(ip_address or "")[:50] or None,
            metadata_json=json.dumps(meta, ensure_ascii=False),
            created_at=now,
        ))
    write_audit(
        "PATIENT_CONSENT_RECORDED", "Patient", patient.patient_code[:100],
        user_email=actor or "SYSTEM", ip_address=(ip_address or "")[:100],
    )
    db.session.flush()
    return current_consents(patient.patient_code)
