"""Organization scoping for patient queries.

scope=None means legacy/unfiltered (jobs, scripts, not-yet-migrated callers).
A non-global scope without an organization is fail-closed (matches nothing).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import false


def scope_enforced() -> bool:
    return os.getenv("TENANT_ENFORCE_PATIENT_SCOPE", "false").strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PatientScope:
    organization_id: str | None = None
    is_global: bool = False


GLOBAL_SCOPE = PatientScope(None, True)


def apply_patient_scope(query, scope: PatientScope | None):
    from app.models.patient import Patient

    if scope is None or scope.is_global:
        return query
    if not scope.organization_id:
        return query.filter(false())
    return query.filter(Patient.organization_id == scope.organization_id)


def patient_in_scope(patient, scope: PatientScope | None) -> bool:
    if patient is None:
        return False
    if scope is None or scope.is_global:
        return True
    return bool(scope.organization_id) and patient.organization_id == scope.organization_id
