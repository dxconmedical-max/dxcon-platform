from flask import Blueprint, request

from app.services.communication_hub_service import (
    EventHubService,
    HubError,
    NotificationCenterService,
    QueueHubService,
    TemplateHubService,
    WebhookHubService,
)
from app.services.notification_service import NotificationService


def _page_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 50)), 1), 200),
    )


def _error(exc):
    return {"error": exc.message}, exc.status_code


hub_notifications_bp = Blueprint("hub_notifications", __name__, url_prefix="/api/v1/notifications")
templates_bp = Blueprint("communication_templates", __name__, url_prefix="/api/v1/templates")
webhooks_bp = Blueprint("communication_webhooks", __name__, url_prefix="/api/v1/webhooks")
events_bp = Blueprint("communication_events", __name__, url_prefix="/api/v1/events")


@hub_notifications_bp.route("/hub", methods=["GET"])
def notification_hub_summary():
    return NotificationCenterService.hub_summary()


@hub_notifications_bp.route("/hub/send", methods=["POST"])
def hub_send():
    data = request.get_json(silent=True) or {}
    if not data.get("recipient") and not data.get("channels"):
        return {"error": "recipient or channels is required"}, 400
    return NotificationCenterService.send_multichannel(data), 201


@hub_notifications_bp.route("/queue", methods=["GET"])
def list_queue():
    return QueueHubService.list_queue(status=request.args.get("status"))


@hub_notifications_bp.route("/queue", methods=["POST"])
def enqueue_notification():
    data = request.get_json(silent=True) or {}
    if not data.get("channel"):
        return {"error": "channel is required"}, 400
    return QueueHubService.enqueue(data), 201


@hub_notifications_bp.route("/queue/process", methods=["POST"])
def process_queue():
    data = request.get_json(silent=True) or {}
    return QueueHubService.process_queue(
        limit=int(data.get("limit") or 10),
        force_fail=bool(data.get("force_fail")),
    )


@hub_notifications_bp.route("/queue/<queue_item_id>/retry", methods=["POST"])
def retry_queue_item(queue_item_id):
    try:
        return QueueHubService.retry(queue_item_id)
    except HubError as exc:
        return _error(exc)


@hub_notifications_bp.route("/deliveries", methods=["GET"])
def list_deliveries():
    return QueueHubService.delivery_tracking()


@hub_notifications_bp.route("/dead-letter", methods=["GET"])
def list_dead_letters():
    return QueueHubService.dead_letters()


@hub_notifications_bp.route("/legacy", methods=["GET"])
def list_legacy_notifications():
    notifications = NotificationService.list_notifications(
        status=request.args.get("status"),
        template_code=request.args.get("template_code"),
    )
    return {
        "count": len(notifications),
        "notifications": [row.to_dict() for row in notifications],
    }


@templates_bp.route("", methods=["GET"])
def list_templates():
    return TemplateHubService.list_templates(channel=request.args.get("channel"))


@templates_bp.route("", methods=["POST"])
def create_template():
    data = request.get_json(silent=True) or {}
    if not data.get("name") and not data.get("body"):
        return {"error": "name or body is required"}, 400
    return TemplateHubService.create(data), 201


@templates_bp.route("/<template_id>", methods=["GET"])
def get_template(template_id):
    try:
        return TemplateHubService.get(template_id)
    except HubError as exc:
        return _error(exc)


@webhooks_bp.route("", methods=["GET"])
def list_webhooks():
    return WebhookHubService.list_webhooks()


@webhooks_bp.route("", methods=["POST"])
def create_webhook():
    data = request.get_json(silent=True) or {}
    try:
        return WebhookHubService.create(data), 201
    except HubError as exc:
        return _error(exc)


@webhooks_bp.route("/deliveries", methods=["GET"])
def webhook_deliveries():
    return WebhookHubService.deliveries(webhook_id=request.args.get("webhook_id"))


@webhooks_bp.route("/<webhook_id>/test", methods=["POST"])
def test_webhook(webhook_id):
    data = request.get_json(silent=True) or {}
    try:
        return WebhookHubService.deliver(webhook_id, data.get("event_type") or "TestEvent", data.get("payload"))
    except HubError as exc:
        return _error(exc)


@events_bp.route("", methods=["GET"])
def list_events():
    page, page_size = _page_args()
    return EventHubService.list_events(
        event_type=request.args.get("event_type"),
        page=page,
        page_size=page_size,
    )


@events_bp.route("/types", methods=["GET"])
def list_event_types():
    return EventHubService.list_event_types()


@events_bp.route("", methods=["POST"])
def emit_event():
    data = request.get_json(silent=True) or {}
    if not data.get("event_type"):
        return {"error": "event_type is required"}, 400
    try:
        return EventHubService.emit(data), 201
    except HubError as exc:
        return _error(exc)
