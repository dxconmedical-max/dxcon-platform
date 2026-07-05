"""MDM API — master data CRUD and import pipeline."""

from __future__ import annotations

from flask import Blueprint, request

from app.extensions.db import db
from app.mdm import ENTITY_LABELS, ENTITY_TYPES
from app.mdm.import_engine import (
    MdmImportError,
    approve_batch,
    commit_batch,
    import_from_bytes,
    rollback_batch,
)
from app.mdm.registry import sample_row, template_columns
from app.mdm.service import (
    MdmServiceError,
    dashboard_stats,
    deactivate_record,
    get_record,
    list_records,
    master_data_report,
    upsert_record,
)
from app.models.mdm import MdmImportBatch

mdm_bp = Blueprint("mdm", __name__, url_prefix="/api/v1/mdm")


@mdm_bp.route("/entities", methods=["GET"])
def list_entities():
    return {
        "count": len(ENTITY_TYPES),
        "data": [
            {"entity_type": e, "label": ENTITY_LABELS.get(e, e), "columns": template_columns(e)}
            for e in ENTITY_TYPES
        ],
    }, 200


@mdm_bp.route("/dashboard", methods=["GET"])
def dashboard():
    return dashboard_stats(), 200


@mdm_bp.route("/report", methods=["GET"])
def report():
    return master_data_report(), 200


@mdm_bp.route("/records/<entity_type>", methods=["GET"])
def records_list(entity_type: str):
    status = request.args.get("status")
    limit = min(int(request.args.get("limit", 100)), 500)
    return {"count": len(list_records(entity_type, status=status, limit=limit)), "data": list_records(entity_type, status=status, limit=limit)}, 200


@mdm_bp.route("/records/<entity_type>/<code>", methods=["GET"])
def records_get(entity_type: str, code: str):
    row = get_record(entity_type, code)
    if not row:
        return {"error": "Not found"}, 404
    return row, 200


@mdm_bp.route("/records/<entity_type>", methods=["POST"])
def records_upsert(entity_type: str):
    try:
        row = upsert_record(entity_type, request.get_json() or {}, actor=request.headers.get("X-Actor"))
        db.session.commit()
        return {"message": "Saved", "record": row}, 201
    except (MdmServiceError, ValueError) as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@mdm_bp.route("/records/<entity_type>/<code>/deactivate", methods=["POST"])
def records_deactivate(entity_type: str, code: str):
    try:
        row = deactivate_record(entity_type, code, actor=request.headers.get("X-Actor"))
        db.session.commit()
        return {"message": "Deactivated", "record": row}, 200
    except MdmServiceError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 404


@mdm_bp.route("/imports/<entity_type>/template", methods=["GET"])
def import_template(entity_type: str):
    cols = template_columns(entity_type)
    sample = sample_row(entity_type)
    return {"entity_type": entity_type, "columns": cols, "sample_row": sample}, 200


@mdm_bp.route("/imports/<entity_type>", methods=["POST"])
def import_upload(entity_type: str):
    if "file" not in request.files:
        return {"error": "file is required"}, 400
    file = request.files["file"]
    content = file.read()
    if not content:
        return {"error": "empty file"}, 400
    auto_approve = request.form.get("auto_approve", "false").lower() == "true"
    auto_commit = request.form.get("auto_commit", "false").lower() == "true"
    try:
        batch = import_from_bytes(
            entity_type,
            content,
            file_name=file.filename or "upload.csv",
            actor=request.headers.get("X-Actor"),
            auto_approve=auto_approve,
            auto_commit=auto_commit,
        )
        db.session.commit()
        return {"message": "Import processed", "batch": batch.to_dict()}, 201
    except (MdmImportError, ValueError) as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@mdm_bp.route("/imports/batches/<batch_id>", methods=["GET"])
def import_batch_detail(batch_id: str):
    batch = MdmImportBatch.query.get(batch_id)
    if not batch:
        return {"error": "Not found"}, 404
    rows = [r.to_dict() for r in batch.rows[:100]]
    payload = batch.to_dict()
    payload["rows"] = rows
    return payload, 200


@mdm_bp.route("/imports/batches/<batch_id>/approve", methods=["POST"])
def import_approve(batch_id: str):
    try:
        batch = approve_batch(batch_id, actor=request.headers.get("X-Actor"))
        db.session.commit()
        return {"message": "Approved", "batch": batch.to_dict()}, 200
    except MdmImportError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@mdm_bp.route("/imports/batches/<batch_id>/commit", methods=["POST"])
def import_commit(batch_id: str):
    try:
        batch = commit_batch(batch_id, actor=request.headers.get("X-Actor"))
        db.session.commit()
        return {"message": "Committed", "batch": batch.to_dict()}, 200
    except MdmImportError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400


@mdm_bp.route("/imports/batches/<batch_id>/rollback", methods=["POST"])
def import_rollback(batch_id: str):
    try:
        batch = rollback_batch(batch_id, actor=request.headers.get("X-Actor"))
        db.session.commit()
        return {"message": "Rolled back", "batch": batch.to_dict()}, 200
    except MdmImportError as exc:
        db.session.rollback()
        return {"error": str(exc)}, 400
