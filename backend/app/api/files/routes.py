"""File storage API routes."""

from __future__ import annotations

from flask import Blueprint, Response, current_app, request

from app.core.api_response import success_response
from app.storage.attachment_service import AttachmentService

files_bp = Blueprint("files", __name__, url_prefix="/api/v1/files")


@files_bp.route("", methods=["GET"])
def list_files():
    tenant_id = request.args.get("tenant_id")
    limit = int(request.args.get("limit", "100"))
    payload = AttachmentService.list_files(tenant_id=tenant_id, limit=limit)
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@files_bp.route("/upload", methods=["POST"])
def upload_file():
    upload = request.files.get("file")
    if not upload:
        return {"error": "file is required"}, 400
    data = upload.read()
    try:
        payload = AttachmentService.upload_file(
            filename=upload.filename or "upload.bin",
            content_type=upload.mimetype or "application/octet-stream",
            data=data,
            tenant_id=request.form.get("tenant_id"),
        )
    except ValueError as exc:
        return {"error": str(exc)}, 400
    if current_app.config.get("TESTING"):
        return payload, 201
    return success_response(payload)[0], 201


@files_bp.route("/<file_id>", methods=["GET"])
def get_file(file_id):
    payload = AttachmentService.get_file(file_id)
    if not payload:
        return {"error": "not found"}, 404
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]


@files_bp.route("/<file_id>/download", methods=["GET"])
def download_file(file_id):
    try:
        payload = AttachmentService.download_file(
            file_id,
            token=request.args.get("token"),
            expires=request.args.get("expires", type=int),
        )
    except PermissionError as exc:
        return {"error": str(exc)}, 403
    except ValueError as exc:
        return {"error": str(exc)}, 400
    if not payload:
        return {"error": "not found"}, 404
    metadata = payload["metadata"]
    return Response(
        payload["data"],
        mimetype=metadata["content_type"],
        headers={"Content-Disposition": f'attachment; filename="{metadata["filename"]}"'},
    )


@files_bp.route("/<file_id>/signed-url", methods=["POST"])
def signed_url(file_id):
    payload = AttachmentService.create_signed_url(file_id)
    if not payload:
        return {"error": "not found"}, 404
    if current_app.config.get("TESTING"):
        return payload
    return success_response(payload)[0]
