"""Laboratory workspace REST API — specimen receive through medical validation."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.lab_workspace.auth import (
    lab_api_admin,
    lab_api_medical,
    lab_api_read,
    lab_api_supervisor,
    lab_api_write,
)
from app.lab_workspace.lis_service import (
    LISImportError,
    get_mappings,
    import_csv,
    import_json,
    lis_adapter_stub,
    list_connectors,
    list_failed_imports,
    list_import_batches,
    retry_failed_import,
    upsert_connector,
    upsert_mapping,
)
from app.lab_workspace.service import (
    LabWorkspaceError,
    assign_processing,
    complete_processing,
    create_accession,
    enter_result_manual,
    get_order_workspace,
    get_released_report_html,
    ingest_analyzer_result,
    lab_security_report,
    lab_workspace_report,
    list_pending_medical_review,
    list_releasable_results,
    mark_qc_failed,
    mark_qc_passed,
    medical_reject,
    medical_reopen,
    medical_validate,
    receive_sample,
    reject_result,
    release_result,
    start_processing,
    status_contract,
    testing_queue,
    validate_result,
    verify_identifiers,
    workspace_dashboard,
)

lab_workspace_bp = Blueprint("lab_workspace", __name__, url_prefix="/api/v1/lab/workspace")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email")


def _err(exc: Exception, code: int = 400):
    db.session.rollback()
    return {"success": False, "error": str(exc)}, code


@lab_workspace_bp.route("/dashboard", methods=["GET"])
@lab_api_read
def dashboard():
    return {"success": True, "data": workspace_dashboard()}, 200


@lab_workspace_bp.route("/status-contract", methods=["GET"])
@lab_api_read
def status_contract_route():
    return {"success": True, "data": status_contract()}, 200


@lab_workspace_bp.route("/orders/<order_code>", methods=["GET"])
@lab_api_read
def order_detail(order_code: str):
    try:
        return {"success": True, "data": get_order_workspace(order_code)}, 200
    except LabWorkspaceError as exc:
        return _err(exc, 404)


@lab_workspace_bp.route("/verify", methods=["POST"])
@lab_api_write
def verify_route():
    payload = request.get_json(silent=True) or {}
    try:
        data = verify_identifiers(
            order_code=payload.get("order_code"),
            sample_code=payload.get("sample_code"),
            barcode_value=payload.get("barcode_value"),
            patient_code=payload.get("patient_code"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/receive", methods=["POST"])
@lab_api_write
def sample_receive():
    payload = request.get_json(silent=True) or {}
    try:
        data = receive_sample(
            sample_code=payload.get("sample_code"),
            order_code=payload.get("order_code"),
            patient_code=payload.get("patient_code"),
            barcode_value=payload.get("barcode_value"),
            received_by=payload.get("received_by", _actor() or "LAB"),
            condition_status=payload.get("condition_status", "acceptable"),
            rejection_reason=payload.get("rejection_reason"),
            note=payload.get("note"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/reject", methods=["POST"])
@lab_api_write
def sample_reject():
    payload = request.get_json(silent=True) or {}
    try:
        data = receive_sample(
            sample_code=payload.get("sample_code"),
            order_code=payload.get("order_code"),
            patient_code=payload.get("patient_code"),
            received_by=payload.get("received_by", _actor() or "LAB"),
            condition_status="rejected",
            rejection_reason=payload.get("rejection_reason") or payload.get("reason") or "other",
            note=payload.get("note") or payload.get("reason"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/accession", methods=["POST"])
@lab_api_write
def accession():
    payload = request.get_json(silent=True) or {}
    try:
        data = create_accession(
            order_code=payload.get("order_code", ""),
            sample_code=payload.get("sample_code"),
            accessioned_by=payload.get("accessioned_by", _actor() or "LAB"),
            laboratory_id=payload.get("laboratory_id"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/assign", methods=["POST"])
@lab_api_write
def assign_route():
    payload = request.get_json(silent=True) or {}
    try:
        data = assign_processing(
            order_code=payload.get("order_code", ""),
            bench_id=payload.get("bench_id"),
            instrument_id=payload.get("instrument_id") or payload.get("instrument"),
            technician=payload.get("technician"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/processing/start", methods=["POST"])
@lab_api_write
def processing_start():
    payload = request.get_json(silent=True) or {}
    try:
        data = start_processing(order_code=payload.get("order_code", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/processing/complete", methods=["POST"])
@lab_api_write
def processing_complete():
    payload = request.get_json(silent=True) or {}
    try:
        data = complete_processing(order_code=payload.get("order_code", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/testing-queue", methods=["GET"])
@lab_api_read
def testing_queue_route():
    result = testing_queue(
        page=int(request.args.get("page", 1)),
        per_page=int(request.args.get("per_page", 50)),
        status=request.args.get("status"),
    )
    return {"success": True, **result}, 200


@lab_workspace_bp.route("/results", methods=["POST"])
@lab_api_write
def results_enter():
    payload = request.get_json(silent=True) or {}
    try:
        data = enter_result_manual(
            payload.get("order_code", ""),
            test_code=payload.get("test_code", ""),
            result_value=payload.get("result_value", ""),
            unit=payload.get("unit"),
            reference_range=payload.get("reference_range"),
            abnormal_flag=payload.get("abnormal_flag"),
            critical_low=payload.get("critical_low"),
            critical_high=payload.get("critical_high"),
            instrument=payload.get("instrument"),
            technician=payload.get("technician"),
            note=payload.get("note"),
            revision_mode=bool(payload.get("revision_mode")),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/results/ingest", methods=["POST"])
@lab_api_write
def results_ingest():
    payload = request.get_json(silent=True) or {}
    try:
        data = ingest_analyzer_result(
            payload.get("order_code", ""),
            test_code=payload.get("test_code", ""),
            result_value=payload.get("result_value", ""),
            unit=payload.get("unit"),
            reference_range=payload.get("reference_range"),
            instrument=payload.get("instrument"),
            technician=payload.get("technician"),
            critical_low=payload.get("critical_low"),
            critical_high=payload.get("critical_high"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/qc/pass", methods=["POST"])
@lab_api_write
def qc_pass():
    payload = request.get_json(silent=True) or {}
    try:
        data = mark_qc_passed(payload.get("order_code", ""), note=payload.get("note"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/qc/fail", methods=["POST"])
@lab_api_write
def qc_fail():
    payload = request.get_json(silent=True) or {}
    try:
        data = mark_qc_failed(payload.get("order_code", ""), note=payload.get("note"), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/validation/approve", methods=["POST"])
@lab_api_supervisor
def validation_approve():
    payload = request.get_json(silent=True) or {}
    try:
        data = validate_result(payload.get("order_code", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/validation/reject", methods=["POST"])
@lab_api_supervisor
def validation_reject():
    payload = request.get_json(silent=True) or {}
    try:
        data = reject_result(
            payload.get("order_code", ""),
            reason=payload.get("reason"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/medical-validation/approve", methods=["POST"])
@lab_api_medical
def medical_validation_approve():
    payload = request.get_json(silent=True) or {}
    try:
        data = medical_validate(
            payload.get("order_code", ""),
            doctor_note=payload.get("doctor_note") or payload.get("note"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/medical-validation/reject", methods=["POST"])
@lab_api_medical
def medical_validation_reject():
    payload = request.get_json(silent=True) or {}
    try:
        data = medical_reject(
            payload.get("order_code", ""),
            reason=payload.get("reason") or payload.get("note"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/medical-validation/reopen", methods=["POST"])
@lab_api_medical
def medical_validation_reopen():
    payload = request.get_json(silent=True) or {}
    try:
        data = medical_reopen(
            payload.get("order_code", ""),
            reason=payload.get("reason") or payload.get("note"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/medical-validation/queue", methods=["GET"])
@lab_api_medical
def medical_validation_queue():
    return {"success": True, "data": {"items": list_pending_medical_review()}}, 200


@lab_workspace_bp.route("/release", methods=["POST"])
@lab_api_medical
def release_result_route():
    payload = request.get_json(silent=True) or {}
    try:
        data = release_result(payload.get("order_code", ""), actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except (LabWorkspaceError, BusinessEngineError) as exc:
        return _err(exc)


@lab_workspace_bp.route("/release/queue", methods=["GET"])
@lab_api_read
def release_queue_route():
    return {"success": True, "data": {"items": list_releasable_results()}}, 200


@lab_workspace_bp.route("/release/<order_code>/html", methods=["GET"])
@lab_api_read
def release_html_route(order_code: str):
    try:
        return {"success": True, "data": get_released_report_html(order_code)}, 200
    except LabWorkspaceError as exc:
        return _err(exc)


@lab_workspace_bp.route("/report", methods=["GET"])
@lab_api_read
def report():
    return {"success": True, "data": lab_workspace_report()}, 200


@lab_workspace_bp.route("/security-report", methods=["GET"])
@lab_api_read
def security_report():
    return {"success": True, "data": lab_security_report()}, 200


# --- LIS ---

@lab_workspace_bp.route("/lis/connectors", methods=["GET"])
@lab_api_read
def lis_connectors_list():
    return {"success": True, **list_connectors(page=int(request.args.get("page", 1)))}, 200


@lab_workspace_bp.route("/lis/connectors", methods=["POST"])
@lab_api_admin
def lis_connectors_create():
    try:
        data = upsert_connector(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LISImportError as exc:
        return _err(exc)


@lab_workspace_bp.route("/lis/connectors/<connector_id>/mappings", methods=["GET"])
@lab_api_read
def lis_mappings(connector_id: str):
    return {"success": True, "data": get_mappings(connector_id)}, 200


@lab_workspace_bp.route("/lis/mappings", methods=["POST"])
@lab_api_supervisor
def lis_mapping_upsert():
    try:
        data = upsert_mapping(request.get_json(silent=True) or {}, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LISImportError as exc:
        return _err(exc)


@lab_workspace_bp.route("/lis/import/csv", methods=["POST"])
@lab_api_write
def lis_import_csv():
    connector_id = request.form.get("connector_id") or (request.get_json(silent=True) or {}).get("connector_id")
    file = request.files.get("file")
    if not connector_id or not file:
        return {"success": False, "error": "connector_id and file required"}, 400
    try:
        data = import_csv(file.read(), connector_id=connector_id, file_name=file.filename, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LISImportError as exc:
        return _err(exc)


@lab_workspace_bp.route("/lis/import/json", methods=["POST"])
@lab_api_write
def lis_import_json_route():
    payload = request.get_json(silent=True) or {}
    connector_id = payload.get("connector_id")
    if not connector_id:
        return {"success": False, "error": "connector_id required"}, 400
    try:
        data = import_json(payload.get("results") or payload, connector_id=connector_id, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LISImportError as exc:
        return _err(exc)


@lab_workspace_bp.route("/lis/import-history", methods=["GET"])
@lab_api_read
def lis_import_history():
    return {"success": True, "data": list_import_batches()}, 200


@lab_workspace_bp.route("/lis/failed-imports", methods=["GET"])
@lab_api_read
def lis_failed_imports():
    return {
        "success": True,
        "data": list_failed_imports(batch_id=request.args.get("batch_id")),
    }, 200


@lab_workspace_bp.route("/lis/failed-imports/<failed_id>/retry", methods=["POST"])
@lab_api_supervisor
def lis_retry_failed(failed_id: str):
    try:
        data = retry_failed_import(failed_id, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LISImportError as exc:
        return _err(exc)


@lab_workspace_bp.route("/lis/adapters/<adapter_type>", methods=["GET"])
@lab_api_read
def lis_adapter(adapter_type: str):
    return {"success": True, "data": lis_adapter_stub(adapter_type.upper())}, 200
