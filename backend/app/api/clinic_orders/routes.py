"""Clinic self-service test requests (phiếu chỉ định).

Clinic side (/api/v1/clinic-orders): a clinic user, only if DxCon switched the clinic on, sends a simple slip:
patient name, birth year, tests, number of sample tubes. The slip never becomes an order by itself.

Staff side (/api/v1/reception/workspace): DxCon staff review the slip and approve it with one click, which
creates the patient and the order through the normal reception pipeline (invoice, queue, collection), or reject it.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from flask import Blueprint, request

from app.api.reception_workspace.routes import _actor, _client_ip, _dxcon_staff_error
from app.core.audit import write_audit
from app.core.authenticated_identity import (
    AuthenticatedIdentity,
    authenticated_actor_email,
    bind_authenticated_identity,
    get_authenticated_identity,
)
from app.core.errors import build_error_response
from app.core.tenant_authorization import AuthorizedTenant, resolve_authorized_tenant
from app.extensions.db import db
from app.models.clinic_order_request import ClinicOrderRequest, ClinicOrderSetting
from app.models.test_catalog import TestCatalog
from app.reception_workspace.auth import reception_api_read, reception_api_write

clinic_orders_bp = Blueprint("clinic_orders", __name__, url_prefix="/api/v1/clinic-orders")
clinic_requests_staff_bp = Blueprint("clinic_requests_staff", __name__, url_prefix="/api/v1/reception/workspace")

# Roles allowed to submit slips. CLINIC_VIEWER (read-only) is deliberately absent.
CLINIC_SUBMIT_ROLES = frozenset(
    {"CLINIC_OWNER", "CLINIC_ADMIN", "PARTNER_OWNER", "PARTNER_CLINIC_OWNER", "ORG_OWNER", "ORG_ADMIN"}
)
STATUSES = frozenset({"NEW", "APPROVED", "REJECTED"})
MAX_TESTS = 30
MAX_TUBES = 20
PER_ORG_PER_DAY = 300
MIN_BIRTH_YEAR = 1900


def _clean(value, limit: int) -> str:
    return " ".join(str(value or "").split())[:limit]


@clinic_orders_bp.before_request
def _require_login():
    if request.method == "OPTIONS":
        return None
    result = bind_authenticated_identity()
    if not isinstance(result, AuthenticatedIdentity):
        return result
    return None


def _org():
    tenant = resolve_authorized_tenant(require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return None, tenant
    if not tenant.organization_id:
        return None, build_error_response("BAD_REQUEST", "organization is required", 400)
    return tenant.organization_id, None


def _can_submit() -> bool:
    identity = get_authenticated_identity()
    if identity is None:
        return False
    roles = {str(identity.platform_role or "").upper(), str(identity.organization_role or "").upper()}
    return bool(roles & CLINIC_SUBMIT_ROLES)


def _enabled(org_id: str) -> bool:
    row = db.session.get(ClinicOrderSetting, org_id)
    return bool(row and row.enabled)


# ---------------------------------------------------------------- clinic side


@clinic_orders_bp.route("/status", methods=["GET"])
def clinic_status():
    org_id, err = _org()
    if err is not None:
        return err
    return {"success": True, "data": {"enabled": _enabled(org_id), "can_submit": _can_submit()}}, 200


def _forbidden_unless_allowed(org_id: str):
    if not _can_submit():
        return build_error_response("FORBIDDEN", "Tài khoản này không có quyền gửi phiếu chỉ định.", 403)
    if not _enabled(org_id):
        return build_error_response(
            "FORBIDDEN", "Phòng khám chưa được bật chức năng tự chỉ định. Vui lòng liên hệ DxCon.", 403
        )
    return None


@clinic_orders_bp.route("/tests", methods=["GET"])
def clinic_tests():
    """Test picker for the slip. Names and codes only: no prices."""
    org_id, err = _org()
    if err is not None:
        return err
    denied = _forbidden_unless_allowed(org_id)
    if denied is not None:
        return denied
    term = _clean(request.args.get("q"), 60)
    query = TestCatalog.query
    if term:
        like = f"%{term}%"
        query = query.filter(TestCatalog.code.ilike(like) | TestCatalog.name.ilike(like))
    rows = query.order_by(TestCatalog.name).limit(30).all()
    return {
        "success": True,
        "data": [{"id": t.id, "code": t.code, "name": t.name, "sample_type": t.sample_type} for t in rows],
    }, 200


def _validate(payload: dict):
    name = _clean(payload.get("patient_name"), 120)
    if len(name) < 2:
        return None, "Vui lòng nhập họ tên bệnh nhân."
    try:
        year = int(payload.get("birth_year"))
    except (TypeError, ValueError):
        return None, "Năm sinh chưa đúng."
    if year < MIN_BIRTH_YEAR or year > datetime.utcnow().year:
        return None, "Năm sinh chưa đúng."
    try:
        tubes = int(payload.get("tube_count"))
    except (TypeError, ValueError):
        return None, "Số ống mẫu chưa đúng."
    if tubes < 1 or tubes > MAX_TUBES:
        return None, f"Số ống mẫu phải từ 1 đến {MAX_TUBES}."
    raw_ids = payload.get("test_ids")
    if not isinstance(raw_ids, list) or not raw_ids:
        return None, "Vui lòng chọn ít nhất một xét nghiệm."
    ids = list(dict.fromkeys(str(i) for i in raw_ids))
    if len(ids) > MAX_TESTS:
        return None, f"Tối đa {MAX_TESTS} xét nghiệm mỗi phiếu."
    tests = TestCatalog.query.filter(TestCatalog.id.in_(ids)).all()
    if len(tests) != len(ids):
        return None, "Có xét nghiệm không tồn tại trong danh mục. Vui lòng chọn lại."
    by_id = {t.id: t for t in tests}
    return {
        "patient_name": name,
        "birth_year": year,
        "tube_count": tubes,
        "tests": [{"id": i, "code": by_id[i].code, "name": by_id[i].name} for i in ids],
    }, None


@clinic_orders_bp.route("/requests", methods=["POST"])
def clinic_request_create():
    org_id, err = _org()
    if err is not None:
        return err
    denied = _forbidden_unless_allowed(org_id)
    if denied is not None:
        return denied
    values, error = _validate(request.get_json(silent=True) or {})
    if error:
        return {"success": False, "error": error}, 400
    since = datetime.utcnow() - timedelta(days=1)
    if ClinicOrderRequest.query.filter(
        ClinicOrderRequest.organization_id == org_id, ClinicOrderRequest.created_at >= since
    ).count() >= PER_ORG_PER_DAY:
        return {"success": False, "error": "Đã đạt giới hạn phiếu trong ngày. Vui lòng liên hệ DxCon."}, 429
    now = datetime.utcnow()
    row = ClinicOrderRequest(
        reference=f"CR-{now:%Y%m%d}-{uuid.uuid4().hex[:6].upper()}",
        organization_id=org_id,
        requested_by=(authenticated_actor_email() or "")[:120] or None,
        patient_name=values["patient_name"],
        birth_year=values["birth_year"],
        tests_json=json.dumps(values["tests"], ensure_ascii=False),
        tube_count=values["tube_count"],
        status="NEW",
        created_at=now,
    )
    db.session.add(row)
    write_audit(
        "CLINIC_ORDER_REQUEST_CREATED", "ClinicOrderRequest", f"{row.reference}|org={org_id}",
        user_email=authenticated_actor_email(), ip_address=_client_ip(),
    )
    db.session.commit()
    return {"success": True, "data": row.to_dict()}, 201


@clinic_orders_bp.route("/requests", methods=["GET"])
def clinic_requests_list():
    org_id, err = _org()
    if err is not None:
        return err
    rows = (
        ClinicOrderRequest.query.filter(ClinicOrderRequest.organization_id == org_id)
        .order_by(ClinicOrderRequest.created_at.desc())
        .limit(100)
        .all()
    )
    return {"success": True, "data": [r.to_dict() for r in rows]}, 200


# ----------------------------------------------------------------- staff side


def _org_names(ids: set[str]) -> dict[str, str]:
    if not ids:
        return {}
    import app.models.partner_foundation as pf

    rows = pf.PartnerOrganization.query.filter(pf.PartnerOrganization.id.in_(list(ids))).all()
    return {r.id: r.organization_name for r in rows}


@clinic_requests_staff_bp.route("/clinic-requests", methods=["GET"])
@reception_api_read
def staff_requests_list():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    status = str(request.args.get("status") or "").upper()
    query = ClinicOrderRequest.query
    if status:
        if status not in STATUSES:
            return {"success": False, "error": "Invalid status"}, 400
        query = query.filter(ClinicOrderRequest.status == status)
    rows = query.order_by(ClinicOrderRequest.created_at.desc()).limit(200).all()
    names = _org_names({r.organization_id for r in rows})
    new_count = ClinicOrderRequest.query.filter(ClinicOrderRequest.status == "NEW").count()
    return {
        "success": True,
        "data": {"items": [r.to_dict(organization_name=names.get(r.organization_id)) for r in rows], "new_count": new_count},
    }, 200


@clinic_requests_staff_bp.route("/clinic-requests/<request_id>/approve", methods=["POST"])
@reception_api_write
def staff_request_approve(request_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    from app.business_engine import service as biz
    from app.business_engine.service import BusinessEngineError
    from app.reception_workspace.consent import consent_gate_enabled
    from app.reception_workspace.service import ReceptionWorkspaceError, create_reception_order
    import app.models.partner_foundation as pf

    row = db.session.query(ClinicOrderRequest).filter_by(id=request_id).with_for_update().first()
    if row is None:
        return {"success": False, "error": "Không tìm thấy phiếu."}, 404
    if row.status != "NEW":
        return {"success": False, "error": "Phiếu này đã được xử lý."}, 409
    if consent_gate_enabled():
        # The consent gate needs a recorded patient consent before any order exists; a slip has none yet.
        return {
            "success": False,
            "code": "consent_required",
            "error": "Hệ thống đang bắt buộc ghi nhận đồng ý xét nghiệm. Hãy tạo bệnh nhân và đơn trong màn hình tiếp nhận.",
        }, 409
    clinic = pf.PartnerOrganization.query.filter_by(
        id=row.organization_id, organization_type="CLINIC", status=pf.ORG_STATUS_ACTIVE
    ).first()
    if clinic is None:
        return {"success": False, "error": "Phòng khám không còn hoạt động."}, 404
    header_org = request.headers.get("X-Organization-ID") or request.headers.get("X-Organization-Id")
    tenant = resolve_authorized_tenant(requested_organization_id=header_org, require_scope=True)
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    collection_org = tenant.organization_id or header_org
    actor = _actor()
    try:
        patient = biz.create_patient(
            full_name=row.patient_name,
            date_of_birth=str(row.birth_year),  # the clinic only supplies the birth year
            actor=actor,
            organization_id=clinic.id,
        )
        result = create_reception_order(
            patient_code=patient.patient_code,
            test_catalog_ids=[t["id"] for t in row.tests],
            note=f"Phiếu phòng khám {row.reference}: {row.tube_count} ống mẫu",
            actor=actor,
            organization_id=clinic.id,
            collection_organization_id=collection_org,
            source_org_code=clinic.organization_code,
        )
    except (ReceptionWorkspaceError, BusinessEngineError) as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400
    row.status = "APPROVED"
    row.order_code = (result.get("order") or {}).get("order_code")
    row.handled_by = (actor or "")[:120] or None
    row.handled_at = datetime.utcnow()
    write_audit("CLINIC_ORDER_REQUEST_APPROVED", "ClinicOrderRequest", row.reference, user_email=actor or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": row.to_dict(organization_name=clinic.organization_name)}, 200


@clinic_requests_staff_bp.route("/clinic-requests/<request_id>/reject", methods=["POST"])
@reception_api_write
def staff_request_reject(request_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    payload = request.get_json(silent=True) or {}
    reason = _clean(payload.get("reason"), 300)
    if len(reason) < 3:
        return {"success": False, "error": "Vui lòng nhập lý do từ chối."}, 400
    row = db.session.query(ClinicOrderRequest).filter_by(id=request_id).with_for_update().first()
    if row is None:
        return {"success": False, "error": "Không tìm thấy phiếu."}, 404
    if row.status != "NEW":
        return {"success": False, "error": "Phiếu này đã được xử lý."}, 409
    actor = _actor()
    row.status = "REJECTED"
    row.reject_reason = reason
    row.handled_by = (actor or "")[:120] or None
    row.handled_at = datetime.utcnow()
    write_audit("CLINIC_ORDER_REQUEST_REJECTED", "ClinicOrderRequest", row.reference, user_email=actor or "SYSTEM", ip_address=_client_ip())
    db.session.commit()
    return {"success": True, "data": row.to_dict()}, 200


@clinic_requests_staff_bp.route("/clinic-order-settings", methods=["GET"])
@reception_api_read
def staff_settings_list():
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    import app.models.partner_foundation as pf

    clinics = (
        pf.PartnerOrganization.query.filter_by(organization_type="CLINIC", status=pf.ORG_STATUS_ACTIVE)
        .order_by(pf.PartnerOrganization.organization_name)
        .all()
    )
    enabled = {s.organization_id: s.enabled for s in ClinicOrderSetting.query.all()}
    return {
        "success": True,
        "data": [
            {"id": c.id, "code": c.organization_code, "name": c.organization_name, "enabled": bool(enabled.get(c.id))}
            for c in clinics
        ],
    }, 200


@clinic_requests_staff_bp.route("/clinic-order-settings/<org_id>", methods=["POST"])
@reception_api_write
def staff_settings_set(org_id: str):
    denied = _dxcon_staff_error()
    if denied is not None:
        return denied
    import app.models.partner_foundation as pf

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload.get("enabled"), bool):
        return {"success": False, "error": "enabled must be true or false"}, 400
    clinic = pf.PartnerOrganization.query.filter_by(id=org_id, organization_type="CLINIC").first()
    if clinic is None:
        return {"success": False, "error": "Không tìm thấy phòng khám."}, 404
    actor = _actor()
    row = db.session.get(ClinicOrderSetting, org_id)
    if row is None:
        row = ClinicOrderSetting(organization_id=org_id)
        db.session.add(row)
    row.enabled = payload["enabled"]
    row.updated_by = (actor or "")[:120] or None
    row.updated_at = datetime.utcnow()
    write_audit(
        "CLINIC_SELF_ORDER_ENABLED" if row.enabled else "CLINIC_SELF_ORDER_DISABLED",
        "ClinicOrderSetting", clinic.organization_code, user_email=actor or "SYSTEM", ip_address=_client_ip(),
    )
    db.session.commit()
    return {"success": True, "data": {"id": clinic.id, "name": clinic.organization_name, "enabled": row.enabled}}, 200
