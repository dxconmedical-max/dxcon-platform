from flask import Blueprint, request

from app.services.notification_service import NotificationError, NotificationService


notifications_bp = Blueprint(
    "notifications",
    __name__,
    url_prefix="/api/v1/notification-legacy",
)

notification_templates_bp = Blueprint(
    "notification_templates",
    __name__,
    url_prefix="/api/v1/notification-templates",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@notifications_bp.route("", methods=["GET"])
def list_notifications():
    notifications = NotificationService.list_notifications(
        status=request.args.get("status"),
        template_code=request.args.get("template_code"),
    )
    return {
        "count": len(notifications),
        "notifications": [row.to_dict() for row in notifications],
    }


@notifications_bp.route("/<notification_id>", methods=["GET"])
def get_notification(notification_id):
    try:
        payload = NotificationService.get_notification(notification_id)
    except NotificationError as exc:
        return {"error": exc.message}, exc.status_code
    return payload


@notifications_bp.route("/send", methods=["POST"])
def send_notification():
    data = request.get_json(silent=True) or {}
    try:
        notification, deliveries = NotificationService.send(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except NotificationError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Notification sent",
        "notification": notification.to_dict(include_recipients=True, include_deliveries=True),
        "delivery_count": len(deliveries),
    }, 201


@notifications_bp.route("/bulk", methods=["POST"])
def bulk_notifications():
    data = request.get_json(silent=True) or {}
    items = data.get("notifications") or data.get("items") or []
    if not items:
        return {"error": "notifications array is required"}, 400
    results = NotificationService.send_bulk(
        items,
        actor_email=_actor_email(),
        ip_address=_client_ip(),
    )
    return {
        "message": "Bulk notifications processed",
        "count": len(results),
        "results": results,
    }, 201


@notifications_bp.route("/test", methods=["POST"])
def test_notification():
    data = request.get_json(silent=True) or {}
    try:
        notification, deliveries = NotificationService.send_test(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except NotificationError as exc:
        return {"error": exc.message}, exc.status_code
    return {
        "message": "Test notification sent",
        "notification": notification.to_dict(include_recipients=True, include_deliveries=True),
        "delivery_count": len(deliveries),
    }, 201


@notification_templates_bp.route("", methods=["GET"])
def list_templates():
    templates = NotificationService.list_templates()
    return {
        "count": len(templates),
        "templates": [template.to_dict() for template in templates],
    }
