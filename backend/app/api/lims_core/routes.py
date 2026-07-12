"""LIMS Core REST API — Release 7.0."""

from __future__ import annotations

from flask import Blueprint, request, session

from app.extensions.db import db
from app.lab_workspace.auth import lab_api_read, lab_api_write
from app.lims_core.service import (
    LimsCoreError,
    create_specimen,
    generate_barcode,
    get_accession,
    get_specimen,
    lims_dashboard,
    list_accessions,
    list_specimens,
    receive_and_accession_specimen,
    specimen_timeline,
    transition_specimen,
    update_specimen,
    verify_barcode,
)

specimens_bp = Blueprint("lims_specimens", __name__, url_prefix="/api/v1/specimens")
barcodes_bp = Blueprint("lims_barcodes", __name__, url_prefix="/api/v1/barcodes")
accessions_bp = Blueprint("lims_accessions", __name__, url_prefix="/api/v1/accessions")
lab_lims_bp = Blueprint("lab_lims", __name__, url_prefix="/api/v1/lab")


def _actor() -> str | None:
    return session.get("email") or request.headers.get("X-Actor") or request.headers.get("X-User-Email")


def _org_id() -> str | None:
    return request.headers.get("X-Organization-ID") or session.get("organization_id")


@lab_lims_bp.route("/dashboard", methods=["GET"])
@lab_api_read
def dashboard():
    return {"success": True, "data": lims_dashboard(organization_id=_org_id())}, 200


@specimens_bp.route("", methods=["GET"])
@lab_api_read
def specimens_list():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 25)), 100)
    data = list_specimens(
        page=page,
        per_page=per_page,
        status=request.args.get("status"),
        order_code=request.args.get("order_code"),
        patient_code=request.args.get("patient_code"),
        organization_id=_org_id() or request.args.get("organization_id"),
    )
    return {"success": True, "data": data}, 200


@specimens_bp.route("", methods=["POST"])
@lab_api_write
def specimens_create():
    payload = request.get_json(silent=True) or {}
    try:
        data = create_specimen(
            order_id=payload.get("order_id"),
            order_code=payload.get("order_code"),
            patient_code=payload.get("patient_code"),
            organization_id=_org_id() or payload.get("organization_id"),
            container_type=payload.get("container_type"),
            volume=payload.get("volume"),
            volume_unit=payload.get("volume_unit", "mL"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LimsCoreError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@specimens_bp.route("/<specimen_id>", methods=["GET"])
@lab_api_read
def specimens_get(specimen_id: str):
    try:
        return {"success": True, "data": get_specimen(specimen_id)}, 200
    except LimsCoreError as exc:
        return {"success": False, "error": str(exc)}, 404


@specimens_bp.route("/<specimen_id>", methods=["PUT", "PATCH"])
@lab_api_write
def specimens_update(specimen_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = update_specimen(specimen_id, patch=payload, actor=_actor())
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LimsCoreError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@specimens_bp.route("/<specimen_id>/transition", methods=["POST"])
@lab_api_write
def specimens_transition(specimen_id: str):
    payload = request.get_json(silent=True) or {}
    try:
        data = transition_specimen(
            specimen_id,
            to_status=payload.get("to_status", ""),
            actor=_actor(),
            note=payload.get("note"),
        )
        db.session.commit()
        return {"success": True, "data": data}, 200
    except LimsCoreError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@specimens_bp.route("/<specimen_id>/timeline", methods=["GET"])
@lab_api_read
def specimens_timeline(specimen_id: str):
    try:
        return {"success": True, "data": specimen_timeline(specimen_id)}, 200
    except LimsCoreError as exc:
        return {"success": False, "error": str(exc)}, 404


@barcodes_bp.route("", methods=["GET"])
@lab_api_read
def barcodes_verify():
    value = request.args.get("value") or request.args.get("barcode")
    if not value:
        return {"success": False, "error": "barcode value required"}, 400
    try:
        return {"success": True, "data": verify_barcode(value)}, 200
    except LimsCoreError as exc:
        return {"success": False, "error": str(exc)}, 404


@barcodes_bp.route("", methods=["POST"])
@lab_api_write
def barcodes_generate():
    payload = request.get_json(silent=True) or {}
    try:
        data = generate_barcode(
            specimen_id=payload.get("specimen_id"),
            formats=payload.get("formats"),
            generated_by=_actor(),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LimsCoreError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@accessions_bp.route("", methods=["GET"])
@lab_api_read
def accessions_list():
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 25)), 100)
    return {"success": True, "data": list_accessions(page=page, per_page=per_page)}, 200


@accessions_bp.route("", methods=["POST"])
@lab_api_write
def accessions_create():
    payload = request.get_json(silent=True) or {}
    try:
        data = receive_and_accession_specimen(
            barcode_value=payload.get("barcode_value", ""),
            operator=payload.get("operator", _actor() or "LAB"),
            rack=payload.get("rack"),
            shelf=payload.get("shelf"),
            batch=payload.get("batch"),
            storage_location_id=payload.get("storage_location_id"),
            laboratory_id=payload.get("laboratory_id"),
            actor=_actor(),
        )
        db.session.commit()
        return {"success": True, "data": data}, 201
    except LimsCoreError as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}, 400


@accessions_bp.route("/<accession_id>", methods=["GET"])
@lab_api_read
def accessions_get(accession_id: str):
    try:
        return {"success": True, "data": get_accession(accession_id)}, 200
    except LimsCoreError as exc:
        return {"success": False, "error": str(exc)}, 404
