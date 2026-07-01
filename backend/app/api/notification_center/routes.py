from flask import Blueprint, request

from app.notifications.notification_service import (
    NotificationCenterError,
    NotificationCenterService,
    NotificationTemplateService,
)


def _error(exc):
    return {"error": exc.message}, exc.status_code


notification_center_bp = Blueprint("notification_center", __name__, url_prefix="/api/v1/notifications")


@notification_center_bp.route("/templates", methods=["GET"])
def list_templates():
    return NotificationTemplateService.list_templates(channel=request.args.get("channel"))


@notification_center_bp.route("/templates", methods=["POST"])
def create_template():
    try:
        return NotificationTemplateService.create_template(request.get_json(silent=True) or {}), 201
    except NotificationCenterError as exc:
        return _error(exc)


@notification_center_bp.route("/templates/<template_id>", methods=["PUT"])
def update_template(template_id):
    try:
        return NotificationTemplateService.update_template(template_id, request.get_json(silent=True) or {})
    except NotificationCenterError as exc:
        return _error(exc)


@notification_center_bp.route("/providers", methods=["GET"])
def list_providers():
    return NotificationCenterService.list_providers()


@notification_center_bp.route("/statistics", methods=["GET"])
def statistics():
    return NotificationCenterService.statistics()


@notification_center_bp.route("", methods=["GET"])
def list_notifications():
    return NotificationCenterService.list_notifications(
        status=request.args.get("status"),
        limit=int(request.args.get("limit") or 100),
    )


@notification_center_bp.route("", methods=["POST"])
def create_notification():
    try:
        return NotificationCenterService.create_notification(request.get_json(silent=True) or {}), 201
    except NotificationCenterError as exc:
        return _error(exc)


@notification_center_bp.route("/<notification_id>", methods=["GET"])
def get_notification(notification_id):
    try:
        return NotificationCenterService.get_notification(notification_id)
    except NotificationCenterError as exc:
        return _error(exc)


@notification_center_bp.route("/<notification_id>/retry", methods=["POST"])
def retry_notification(notification_id):
    try:
        return NotificationCenterService.retry_notification(notification_id)
    except NotificationCenterError as exc:
        return _error(exc)
