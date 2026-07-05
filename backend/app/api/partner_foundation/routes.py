"""Partner foundation REST API — Sprint 005."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.core.authz import roles_required
from app.extensions.db import db
from app.partner_foundation.security import PARTNER_READ_ROLES, PARTNER_WRITE_ROLES
from app.partner_foundation.service import (
    PartnerFoundationError,
    assign_organization_price_list,
    backfill_users_to_internal_org,
    disable_organization_user,
    ensure_default_organization,
    invite_organization_user,
    organization_dashboard,
    partner_foundation_report,
    permission_matrix,
    query_organizations,
    rbac_report,
    seed_organization_roles,
    tenant_security_report,
    upsert_organization,
    upsert_partner_contract,
)
from app.models.partner_foundation import OrganizationPriceList, OrganizationUser, PartnerContract

partner_foundation_bp = Blueprint("partner_foundation", __name__, url_prefix="/api/v1/partner")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email")


@partner_foundation_bp.route("/bootstrap", methods=["POST"])
@roles_required("SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN")
def bootstrap():
    ensure_default_organization()
    seed_organization_roles()
    linked = backfill_users_to_internal_org()
    db.session.commit()
    return {"success": True, "data": {"users_linked": linked}}, 200


@partner_foundation_bp.route("/organizations", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def organizations_list():
    result = query_organizations(
        search=request.args.get("search") or request.args.get("q"),
        organization_type=request.args.get("organization_type"),
        status=request.args.get("status"),
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", request.args.get("limit", 25))),
        sort=request.args.get("sort", "organization_code"),
        sort_dir=request.args.get("sort_dir", "asc"),
    )
    return {"success": True, **result}, 200


@partner_foundation_bp.route("/organizations", methods=["POST"])
@roles_required(*PARTNER_WRITE_ROLES)
def organizations_create():
    try:
        row = upsert_organization(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": row}, 201
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/organizations/<org_id>", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def organizations_get(org_id: str):
    from app.models.partner_foundation import PartnerOrganization

    row = PartnerOrganization.query.get(org_id)
    if not row:
        return {"success": False, "error": "not found"}, 404
    return {"success": True, "data": row.to_dict()}, 200


@partner_foundation_bp.route("/organizations/<org_id>", methods=["PUT", "PATCH"])
@roles_required(*PARTNER_WRITE_ROLES)
def organizations_update(org_id: str):
    from app.models.partner_foundation import PartnerOrganization

    row = PartnerOrganization.query.get(org_id)
    if not row:
        return {"success": False, "error": "not found"}, 404
    payload = request.get_json(silent=True) or {}
    payload.setdefault("organization_code", row.organization_code)
    payload.setdefault("organization_name", row.organization_name)
    try:
        data = upsert_organization(payload, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/users", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def partner_users_list():
    org_id = request.args.get("organization_id")
    query = OrganizationUser.query
    if org_id:
        query = query.filter_by(organization_id=org_id)
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("per_page", 25)), 1), 500)
    total = query.count()
    rows = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "success": True,
        "data": [r.to_dict() for r in rows],
        "pagination": {"page": page, "per_page": per_page, "total": total},
    }, 200


@partner_foundation_bp.route("/users/invite", methods=["POST"])
@roles_required(*PARTNER_WRITE_ROLES)
def partner_users_invite():
    payload = request.get_json(silent=True) or {}
    try:
        row = invite_organization_user(
            payload.get("organization_id", ""),
            payload.get("user_id", ""),
            role_code=payload.get("role_code", "VIEWER"),
            invited_by=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": row}, 201
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/users/<organization_id>/<user_id>/disable", methods=["POST"])
@roles_required(*PARTNER_WRITE_ROLES)
def partner_users_disable(organization_id: str, user_id: str):
    try:
        row = disable_organization_user(organization_id, user_id, actor=_actor())
        db.session.commit()
        return {"success": True, "data": row}, 200
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/contracts", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def contracts_list():
    org_id = request.args.get("organization_id")
    query = PartnerContract.query
    if org_id:
        query = query.filter_by(organization_id=org_id)
    rows = query.limit(int(request.args.get("limit", 100))).all()
    return {"success": True, "data": [r.to_dict() for r in rows]}, 200


@partner_foundation_bp.route("/contracts", methods=["POST"])
@roles_required(*PARTNER_WRITE_ROLES)
def contracts_create():
    try:
        row = upsert_partner_contract(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": row}, 201
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/price-lists", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def price_lists_list():
    org_id = request.args.get("organization_id")
    query = OrganizationPriceList.query
    if org_id:
        query = query.filter_by(organization_id=org_id)
    rows = query.limit(int(request.args.get("limit", 100))).all()
    return {"success": True, "data": [r.to_dict() for r in rows]}, 200


@partner_foundation_bp.route("/price-lists", methods=["POST"])
@roles_required(*PARTNER_WRITE_ROLES)
def price_lists_create():
    try:
        row = assign_organization_price_list(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": row}, 201
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/permissions", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def permissions():
    return {"success": True, "data": permission_matrix()}, 200


@partner_foundation_bp.route("/dashboard/<portal>", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def dashboard(portal: str):
    org_id = request.args.get("organization_id") or session.get("organization_id")
    if not org_id:
        org = ensure_default_organization()
        org_id = org.id
    try:
        data = organization_dashboard(org_id, portal)
        return {"success": True, "data": data}, 200
    except PartnerFoundationError as exc:
        return {"success": False, "error": str(exc)}, 400


@partner_foundation_bp.route("/report", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def report():
    return {"success": True, "data": partner_foundation_report()}, 200


@partner_foundation_bp.route("/rbac-report", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def rbac_report_route():
    return {"success": True, "data": rbac_report()}, 200


@partner_foundation_bp.route("/tenant-security-report", methods=["GET"])
@roles_required(*PARTNER_READ_ROLES)
def tenant_security_report_route():
    return {"success": True, "data": tenant_security_report()}, 200
