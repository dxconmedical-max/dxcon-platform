"""Mandatory tenant / membership isolation (P0-C).

Canonical flow:

  Authenticated identity (P0-A)
        ↓
  Organization memberships (OrganizationUser)
        ↓
  Optional client selector (header / query / body)
        ↓
  Membership validation (active only)
        ↓
  Authorized organization scope
        ↓
  Resource ownership check
        ↓
  ALLOW / 403 / 404

Client-supplied organization_id / clinic_id / doctor_id / patient_id are
selectors only — never trusted without membership (or ownership) validation.

Fail-closed: tenant-scoped endpoints with no valid membership/scope must NOT
query all tenants.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Iterable

from flask import g, request, session

from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.errors import build_error_response
from app.partner_foundation.rbac import GLOBAL_ORG_BYPASS_ROLES
from app.services.auth_context_service import list_user_memberships


_G_TENANT_KEY = "authorized_tenant"
_G_TENANT_REQUEST_KEY = "authorized_tenant_request"


@dataclass(frozen=True)
class AuthorizedTenant:
    """Server-resolved tenant scope for the current request."""

    organization_id: str | None
    organization_ids: frozenset[str]
    membership_id: str | None
    organization_role: str | None
    is_global_scope: bool  # SUPER_ADMIN / SYSTEM_ADMIN without explicit org


class TenantAuthorizationError(Exception):
    def __init__(self, message: str, status_code: int = 403, code: str = "FORBIDDEN"):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code

    def as_response(self):
        return build_error_response(self.code, self.message, self.status_code)


def _forbidden(message: str = "Organization access denied", code: str = "FORBIDDEN"):
    return build_error_response(code, message, 403)


def _not_found(message: str = "Resource not found"):
    return build_error_response("NOT_FOUND", message, 404)


def _bind_identity() -> AuthenticatedIdentity | tuple:
    identity = get_authenticated_identity()
    if identity is not None:
        return identity
    return bind_authenticated_identity()


def _active_memberships(user) -> list[dict]:
    memberships = list_user_memberships(user) or []
    return [m for m in memberships if m.get("membership_status") == "active"]


def membership_organization_ids(user) -> frozenset[str]:
    return frozenset(
        m["organization_id"]
        for m in _active_memberships(user)
        if m.get("organization_id")
    )


def client_requested_organization_id() -> str | None:
    """Read client org selector — not trusted until validated."""
    raw = (
        request.headers.get("X-Organization-ID")
        or request.headers.get("X-Organization-Id")
        or request.args.get("organization_id")
    )
    if not raw and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        data = request.get_json(silent=True) or {}
        raw = data.get("organization_id")
    return (str(raw).strip() if raw else None) or None


def client_requested_clinic_id() -> str | None:
    raw = request.args.get("clinic_id") or request.headers.get("X-Clinic-Id")
    if not raw and request.method in {"POST", "PUT", "PATCH"}:
        data = request.get_json(silent=True) or {}
        raw = data.get("clinic_id")
    return (str(raw).strip() if raw else None) or None


def client_requested_doctor_id() -> str | None:
    raw = request.args.get("doctor_id") or request.headers.get("X-Doctor-Id")
    if not raw and request.method in {"POST", "PUT", "PATCH"}:
        data = request.get_json(silent=True) or {}
        raw = data.get("doctor_id")
    return (str(raw).strip() if raw else None) or None


def client_requested_patient_id() -> str | None:
    raw = (
        request.args.get("patient_id")
        or request.headers.get("X-Patient-Id")
        or request.headers.get("X-Patient-Code")
    )
    if not raw and request.method in {"POST", "PUT", "PATCH"}:
        data = request.get_json(silent=True) or {}
        raw = data.get("patient_id") or data.get("patient_code")
    return (str(raw).strip() if raw else None) or None


def _is_platform_global(platform_role: str) -> bool:
    return (platform_role or "").upper() in GLOBAL_ORG_BYPASS_ROLES


def resolve_authorized_tenant(
    *,
    requested_organization_id: str | None = None,
    require_scope: bool = True,
) -> AuthorizedTenant | tuple:
    """Resolve membership-validated organization scope.

    SUPER_ADMIN / SYSTEM_ADMIN may operate globally when no org is requested.
    Ordinary ADMIN and all other roles require an active membership.
    Missing scope on tenant-scoped calls → 403 (fail-closed).
    """
    identity = _bind_identity()
    if not isinstance(identity, AuthenticatedIdentity):
        return identity

    from flask import has_request_context

    if has_request_context():
        cached = getattr(g, _G_TENANT_KEY, None)
        try:
            current = request._get_current_object()
        except RuntimeError:
            current = None
        if (
            isinstance(cached, AuthorizedTenant)
            and getattr(g, _G_TENANT_REQUEST_KEY, None) is current
            and requested_organization_id in (None, cached.organization_id)
        ):
            return cached

    user = identity.user
    if user is None:
        return _forbidden("User not found", "UNAUTHORIZED")

    requested = requested_organization_id or client_requested_organization_id()
    active_memberships = _active_memberships(user)
    org_ids = frozenset(m["organization_id"] for m in active_memberships if m.get("organization_id"))

    # Prefer user's active organization pointer when it is still an active membership.
    preferred = None
    if user.organization_id and user.organization_id in org_ids:
        preferred = user.organization_id
    elif identity.organization_id and identity.organization_id in org_ids:
        preferred = identity.organization_id
    elif active_memberships:
        preferred = active_memberships[0].get("organization_id")

    if _is_platform_global(identity.platform_role):
        if requested:
            selected = next((m for m in active_memberships if m.get("organization_id") == requested), None)
            tenant = AuthorizedTenant(
                organization_id=requested,
                organization_ids=org_ids | frozenset({requested}),
                membership_id=selected.get("membership_id") if selected else None,
                organization_role=selected.get("role_code") if selected else None,
                is_global_scope=False,
            )
        else:
            if require_scope and not preferred:
                # Global platform operators may omit org for cross-tenant admin tools.
                tenant = AuthorizedTenant(
                    organization_id=None,
                    organization_ids=org_ids,
                    membership_id=None,
                    organization_role=None,
                    is_global_scope=True,
                )
            else:
                selected = next(
                    (m for m in active_memberships if m.get("organization_id") == preferred),
                    None,
                )
                tenant = AuthorizedTenant(
                    organization_id=preferred,
                    organization_ids=org_ids,
                    membership_id=selected.get("membership_id") if selected else None,
                    organization_role=selected.get("role_code") if selected else None,
                    is_global_scope=preferred is None,
                )
        return _store_tenant(tenant)

    # Non-global roles: membership required (ADMIN included — no automatic cross-tenant).
    if not org_ids:
        return _forbidden("No active organization membership", "ORGANIZATION_REQUIRED")

    if requested:
        if requested not in org_ids:
            return _forbidden("Organization membership not found", "MEMBERSHIP_NOT_FOUND")
        selected = next(m for m in active_memberships if m.get("organization_id") == requested)
        tenant = AuthorizedTenant(
            organization_id=requested,
            organization_ids=org_ids,
            membership_id=selected.get("membership_id"),
            organization_role=selected.get("role_code"),
            is_global_scope=False,
        )
        return _store_tenant(tenant)

    if require_scope and not preferred:
        return _forbidden("Organization scope required", "ORGANIZATION_REQUIRED")

    selected = next((m for m in active_memberships if m.get("organization_id") == preferred), None)
    if preferred and selected is None:
        return _forbidden("Organization membership not found", "MEMBERSHIP_NOT_FOUND")

    tenant = AuthorizedTenant(
        organization_id=preferred,
        organization_ids=org_ids,
        membership_id=selected.get("membership_id") if selected else None,
        organization_role=selected.get("role_code") if selected else None,
        is_global_scope=False,
    )
    return _store_tenant(tenant)


def _store_tenant(tenant: AuthorizedTenant) -> AuthorizedTenant:
    from flask import has_request_context

    setattr(g, _G_TENANT_KEY, tenant)
    if has_request_context():
        try:
            setattr(g, _G_TENANT_REQUEST_KEY, request._get_current_object())
        except RuntimeError:
            pass
    # Keep session active org aligned when membership-validated.
    if tenant.organization_id and session is not None:
        try:
            session["organization_id"] = tenant.organization_id
            session["active_organization_id"] = tenant.organization_id
        except Exception:
            # Session may be immutable outside a request; scope still returned.
            return tenant
    return tenant


def get_authorized_tenant() -> AuthorizedTenant | None:
    tenant = getattr(g, _G_TENANT_KEY, None)
    return tenant if isinstance(tenant, AuthorizedTenant) else None


def require_organization_scope(fn=None, *, require_scope: bool = True):
    """Decorator: bind authenticated identity + membership-validated org scope."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            result = resolve_authorized_tenant(require_scope=require_scope)
            if not isinstance(result, AuthorizedTenant):
                return result
            return view(*args, **kwargs)

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator


def assert_organization_allows(
    record_org_id: str | None,
    *,
    tenant: AuthorizedTenant | None = None,
    not_found_on_mismatch: bool = True,
) -> None:
    """Raise TenantAuthorizationError if record is outside authorized scope."""
    tenant = tenant or get_authorized_tenant()
    if tenant is None:
        raise TenantAuthorizationError("Organization scope required", 403, "ORGANIZATION_REQUIRED")
    if tenant.is_global_scope:
        return
    if not record_org_id:
        # Unstamped resources are not visible to tenant-scoped users (fail-closed).
        raise TenantAuthorizationError(
            "Resource not found" if not_found_on_mismatch else "Resource has no organization",
            404 if not_found_on_mismatch else 403,
            "NOT_FOUND" if not_found_on_mismatch else "FORBIDDEN",
        )
    allowed = set(tenant.organization_ids)
    if tenant.organization_id:
        allowed.add(tenant.organization_id)
    if record_org_id not in allowed:
        raise TenantAuthorizationError(
            "Resource not found" if not_found_on_mismatch else "Cross-tenant access denied",
            404 if not_found_on_mismatch else 403,
            "NOT_FOUND" if not_found_on_mismatch else "FORBIDDEN",
        )


def apply_authorized_organization_filter(query, model, *, column_name: str = "organization_id"):
    """Fail-closed query filter using authorized tenant scope."""
    tenant = get_authorized_tenant()
    if tenant is None:
        result = resolve_authorized_tenant(require_scope=True)
        if not isinstance(result, AuthorizedTenant):
            raise TenantAuthorizationError("Organization scope required", 403, "ORGANIZATION_REQUIRED")
        tenant = result
    if tenant.is_global_scope:
        return query
    col = getattr(model, column_name, None)
    if col is None:
        raise TenantAuthorizationError(
            f"Model {model.__name__} has no {column_name} for tenant scoping",
            403,
            "TENANT_SCOPE_UNSUPPORTED",
        )
    org_ids = set(tenant.organization_ids)
    if tenant.organization_id:
        org_ids.add(tenant.organization_id)
    if not org_ids:
        raise TenantAuthorizationError("Organization scope required", 403, "ORGANIZATION_REQUIRED")
    return query.filter(col.in_(sorted(org_ids)))


def authorize_clinic_id(clinic_id: str | None) -> str | tuple:
    """Validate clinic selector against membership (via partner_id / organization_id)."""
    if not clinic_id:
        return build_error_response("BAD_REQUEST", "clinic_id is required", 400)

    tenant = resolve_authorized_tenant(require_scope=False)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant

    from app.models.clinic_profile import ClinicProfile

    profile = ClinicProfile.query.filter_by(clinic_id=clinic_id).first()
    if not profile:
        return _not_found("Clinic not found")

    if tenant.is_global_scope:
        return clinic_id

    # Bind clinic to partner-foundation org via partner_id or organization_id stamp.
    clinic_org_keys = {
        k for k in (profile.partner_id, profile.organization_id) if k
    }
    if not clinic_org_keys:
        return _forbidden("Clinic is not linked to an organization")

    allowed = set(tenant.organization_ids)
    if tenant.organization_id:
        allowed.add(tenant.organization_id)
    if clinic_org_keys.isdisjoint(allowed):
        return _not_found("Clinic not found")
    return clinic_id


def authorize_doctor_id(doctor_id: str | None) -> str | tuple:
    """Validate doctor selector: ownership by email or clinic membership link."""
    if not doctor_id:
        return build_error_response("BAD_REQUEST", "doctor_id is required", 400)

    identity = _bind_identity()
    if not isinstance(identity, AuthenticatedIdentity):
        return identity

    tenant = resolve_authorized_tenant(require_scope=False)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant

    from app.models.clinic_doctor import ClinicDoctor
    from app.models.clinic_profile import ClinicProfile
    from app.models.doctor_profile import DoctorProfile

    profile = DoctorProfile.query.filter_by(doctor_id=doctor_id).first()
    if not profile:
        return _not_found("Doctor not found")

    if tenant.is_global_scope:
        return doctor_id

    # Self-binding by verified email.
    if profile.email and identity.email and profile.email.lower() == identity.email.lower():
        return doctor_id

    # Doctor linked to a clinic belonging to authorized organizations.
    links = ClinicDoctor.query.filter_by(doctor_id=doctor_id, status="ACTIVE").all()
    clinic_ids = [link.clinic_id for link in links]
    if clinic_ids:
        clinics = ClinicProfile.query.filter(ClinicProfile.clinic_id.in_(clinic_ids)).all()
        allowed = set(tenant.organization_ids)
        if tenant.organization_id:
            allowed.add(tenant.organization_id)
        for clinic in clinics:
            keys = {k for k in (clinic.partner_id, clinic.organization_id) if k}
            if keys & allowed:
                return doctor_id

    return _not_found("Doctor not found")


def authorize_patient_id(patient_id: str | None) -> str | tuple:
    """Validate patient selector: own record, or clinic-patient in authorized orgs."""
    if not patient_id:
        return build_error_response("BAD_REQUEST", "patient_id is required", 400)

    identity = _bind_identity()
    if not isinstance(identity, AuthenticatedIdentity):
        return identity

    tenant = resolve_authorized_tenant(require_scope=False)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant

    from app.models.clinic_patient import ClinicPatient
    from app.models.clinic_profile import ClinicProfile
    from app.models.patient import Patient

    patient = Patient.query.get(patient_id)
    if not patient:
        return _not_found("Patient not found")

    if tenant.is_global_scope:
        return patient_id

    # Patient self-access via email or session binding.
    if patient.email and identity.email and patient.email.lower() == identity.email.lower():
        return patient_id
    session_patient = session.get("patient_id") or session.get("patient_code")
    if session_patient and str(session_patient) == str(patient_id):
        return patient_id

    # Clinical staff: patient must be linked to an authorized clinic.
    if identity.platform_role in {
        "ADMIN",
        "RECEPTION",
        "DOCTOR",
        "LAB",
        "COLLECTOR",
        "ACCOUNTING",
        "CLINIC_ADMIN",
        "CLINIC_OWNER",
    }:
        links = ClinicPatient.query.filter_by(patient_id=patient_id).all()
        clinic_ids = [link.clinic_id for link in links]
        if clinic_ids:
            clinics = ClinicProfile.query.filter(ClinicProfile.clinic_id.in_(clinic_ids)).all()
            allowed = set(tenant.organization_ids)
            if tenant.organization_id:
                allowed.add(tenant.organization_id)
            for clinic in clinics:
                keys = {k for k in (clinic.partner_id, clinic.organization_id) if k}
                if keys & allowed:
                    return patient_id

    return _not_found("Patient not found")


def authorize_partner_scope(partner_or_org_id: str | None) -> str | None | tuple:
    """Validate partner_id / organization_id used as operational tenant stamp."""
    tenant = resolve_authorized_tenant(
        requested_organization_id=partner_or_org_id,
        require_scope=True,
    )
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    if tenant.is_global_scope:
        return partner_or_org_id  # may be None for global list
    return tenant.organization_id


def scoped_partner_ids(tenant: AuthorizedTenant | None = None) -> frozenset[str] | None:
    """Return org ids for partner_id filtering, or None for global SUPER_ADMIN scope."""
    tenant = tenant or get_authorized_tenant()
    if tenant is None:
        result = resolve_authorized_tenant(require_scope=True)
        if not isinstance(result, AuthorizedTenant):
            return frozenset()
        tenant = result
    if tenant.is_global_scope:
        return None
    ids = set(tenant.organization_ids)
    if tenant.organization_id:
        ids.add(tenant.organization_id)
    return frozenset(ids)


def filter_items_by_partner(items: Iterable[dict], *, partner_key: str = "partner_id") -> list[dict]:
    """Fail-closed in-memory filter for payloads stamped with partner_id."""
    allowed = scoped_partner_ids()
    if allowed is None:
        return list(items)
    if not allowed:
        return []
    out = []
    for item in items:
        partner = item.get(partner_key)
        if partner and partner in allowed:
            out.append(item)
        # Unstamped rows are hidden for tenant users (fail-closed).
    return out


def require_authorized_partner_scope(
    *,
    requested_organization_id: str | None = None,
    require_scope: bool = True,
) -> tuple[AuthorizedTenant, frozenset[str] | None] | tuple:
    """Resolve tenant + partner_id filter set for list endpoints.

    On success returns ``(AuthorizedTenant, partner_ids|None)``.
    On failure returns an error response ``(body, status)`` — callers MUST check
    ``isinstance(result[0], AuthorizedTenant)`` (not merely ``isinstance(result, tuple)``).
    """
    tenant = resolve_authorized_tenant(
        requested_organization_id=requested_organization_id,
        require_scope=require_scope,
    )
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    return (tenant, scoped_partner_ids(tenant))


def assert_partner_allows(
    partner_id: str | None,
    *,
    tenant: AuthorizedTenant | None = None,
    not_found_on_mismatch: bool = True,
) -> None:
    """Assert a partner_id-stamped resource is inside authorized scope."""
    assert_organization_allows(
        partner_id,
        tenant=tenant,
        not_found_on_mismatch=not_found_on_mismatch,
    )


def authorize_partner_record(
    partner_id: str | None,
    *,
    not_found_on_mismatch: bool = True,
) -> AuthorizedTenant | tuple:
    """Resolve tenant and assert partner stamp. Returns tenant or error response."""
    tenant = resolve_authorized_tenant(require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    try:
        assert_partner_allows(
            partner_id,
            tenant=tenant,
            not_found_on_mismatch=not_found_on_mismatch,
        )
    except TenantAuthorizationError as exc:
        return exc.as_response()
    return tenant


def medical_order_partner_id(medical_order_id: str | None) -> str | None:
    if not medical_order_id:
        return None
    from app.models.medical_order import MedicalOrder

    order = MedicalOrder.query.get(medical_order_id)
    return order.partner_id if order else None
