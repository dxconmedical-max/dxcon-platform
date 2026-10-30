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


def is_internal_org(organization_id: str | None) -> bool:
    """True for the DxCon operating organization (platform staff see all tenants). Fails closed."""
    if not organization_id:
        return False
    try:
        from sqlalchemy import text

        from app.extensions.db import db

        row = db.session.execute(
            text("select organization_type from organizations where id = :i"), {"i": organization_id}
        ).first()
        return bool(row) and str(row[0] or "").upper() == "DXCON_INTERNAL"
    except Exception:
        return False


def resolve_patient_scope():
    """Return (scope, error_response). (None, None) means enforcement is off (legacy behaviour)."""
    if not scope_enforced():
        return None, None
    from app.core.tenant_authorization import AuthorizedTenant, resolve_authorized_tenant

    tenant = resolve_authorized_tenant(requested_organization_id=None, require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return None, tenant
    if tenant.is_global_scope or is_internal_org(tenant.organization_id):
        return GLOBAL_SCOPE, None
    return PatientScope(tenant.organization_id), None
