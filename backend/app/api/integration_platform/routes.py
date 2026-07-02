from flask import Blueprint, request

from app.services.integration_platform_service import (
    EventPlatformService,
    IntegrationError,
    IntegrationPlatformService,
    IntegrationQueueService,
    SandboxService,
    WebhookEngineService,
)
from app.plugins.plugin_manager import PluginManager


def _page_args():
    return (
        max(int(request.args.get("page", 1)), 1),
        min(max(int(request.args.get("page_size", 50)), 1), 200),
    )


def _error(exc):
    return {"error": exc.message}, exc.status_code


plugins_bp = Blueprint("integration_plugins", __name__, url_prefix="/api/v1/plugins")
events_bp = Blueprint("integration_events", __name__, url_prefix="/api/v1/events")
webhooks_bp = Blueprint("integration_webhooks", __name__, url_prefix="/api/v1/webhooks")
queue_bp = Blueprint("integration_queue", __name__, url_prefix="/api/v1/integration-queue")
sandbox_bp = Blueprint("integration_sandbox", __name__, url_prefix="/api/v1/sandbox")


@plugins_bp.route("", methods=["GET"])
def list_plugins():
    return PluginManager.list_plugins()


@plugins_bp.route("/<plugin_id>", methods=["GET"])
def get_plugin(plugin_id):
    try:
        return PluginManager.get_plugin(plugin_id)
    except KeyError as exc:
        return _error(IntegrationError(str(exc), 404))


@plugins_bp.route("/<plugin_id>/enable", methods=["POST"])
def enable_plugin(plugin_id):
    data = request.get_json(silent=True) or {}
    try:
        result = PluginManager.enable(plugin_id, data.get("config"))
        if isinstance(result, dict) and result.get("valid") is False:
            return {"error": "Invalid plugin config", "details": result}, 422
        return result
    except KeyError as exc:
        return _error(IntegrationError(str(exc), 404))


@plugins_bp.route("/<plugin_id>/disable", methods=["POST"])
def disable_plugin(plugin_id):
    try:
        return PluginManager.disable(plugin_id)
    except KeyError as exc:
        return _error(IntegrationError(str(exc), 404))


@plugins_bp.route("/<plugin_id>/health", methods=["GET"])
def plugin_health(plugin_id):
    try:
        return PluginManager.health_check(plugin_id)
    except KeyError as exc:
        return _error(IntegrationError(str(exc), 404))


@events_bp.route("", methods=["GET"])
def list_events():
    page, page_size = _page_args()
    return EventPlatformService.list_events(
        event_type=request.args.get("event_type"),
        page=page,
        page_size=page_size,
    )


@events_bp.route("/test", methods=["POST"])
def test_event():
    data = request.get_json(silent=True) or {}
    return EventPlatformService.test_event(data), 201


@events_bp.route("/<event_id>", methods=["GET"])
def get_event(event_id):
    try:
        return EventPlatformService.get_event(event_id)
    except IntegrationError as exc:
        return _error(exc)


@webhooks_bp.route("", methods=["GET"])
def list_webhooks():
    return WebhookEngineService.list_webhooks()


@webhooks_bp.route("", methods=["POST"])
def create_webhook():
    data = request.get_json(silent=True) or {}
    try:
        return WebhookEngineService.create(data), 201
    except IntegrationError as exc:
        return _error(exc)


@webhooks_bp.route("/<webhook_id>", methods=["GET"])
def get_webhook(webhook_id):
    try:
        return WebhookEngineService.get(webhook_id)
    except IntegrationError as exc:
        return _error(exc)


@webhooks_bp.route("/<webhook_id>/test", methods=["POST"])
def test_webhook(webhook_id):
    data = request.get_json(silent=True) or {}
    try:
        return WebhookEngineService.test(webhook_id, data)
    except IntegrationError as exc:
        return _error(exc)


@webhooks_bp.route("/deliveries", methods=["GET"])
def list_deliveries():
    return WebhookEngineService.list_deliveries(webhook_id=request.args.get("webhook_id"))


@webhooks_bp.route("/deliveries/<delivery_id>/retry", methods=["POST"])
def retry_delivery(delivery_id):
    try:
        return WebhookEngineService.retry_delivery(delivery_id)
    except IntegrationError as exc:
        return _error(exc)


@webhooks_bp.route("/replay", methods=["POST"])
def replay_webhook():
    from app.webhooks.replay import WebhookReplayService

    data = request.get_json(silent=True) or {}
    try:
        return WebhookReplayService.replay_from_payload(data)
    except IntegrationError as exc:
        return _error(exc)


@queue_bp.route("/jobs", methods=["GET"])
def list_jobs():
    return IntegrationQueueService.list_jobs(status=request.args.get("status"))


@queue_bp.route("/jobs", methods=["POST"])
def create_job():
    data = request.get_json(silent=True) or {}
    return IntegrationQueueService.create(data), 201


@queue_bp.route("/jobs/<job_id>/retry", methods=["POST"])
def retry_job(job_id):
    try:
        return IntegrationQueueService.retry_job(job_id)
    except IntegrationError as exc:
        return _error(exc)


@queue_bp.route("/dead-letters", methods=["GET"])
def list_dead_letters():
    return IntegrationQueueService.list_dead_letters()


@queue_bp.route("/dead-letters/<dead_letter_id>/replay", methods=["POST"])
def replay_dead_letter(dead_letter_id):
    try:
        return IntegrationQueueService.replay_dead_letter(dead_letter_id)
    except IntegrationError as exc:
        return _error(exc)


@sandbox_bp.route("/status", methods=["GET"])
def sandbox_status():
    return SandboxService.status()


@sandbox_bp.route("/lis/result", methods=["POST"])
def sandbox_lis_result():
    data = request.get_json(silent=True) or {}
    return SandboxService.lis_result(data), 201


@sandbox_bp.route("/his/patient", methods=["POST"])
def sandbox_his_patient():
    data = request.get_json(silent=True) or {}
    return SandboxService.his_patient(data), 201


@sandbox_bp.route("/payment/callback", methods=["POST"])
def sandbox_payment_callback():
    data = request.get_json(silent=True) or {}
    return SandboxService.payment_callback(data), 201


@sandbox_bp.route("/webhook/test", methods=["POST"])
def sandbox_webhook_test():
    data = request.get_json(silent=True) or {}
    try:
        return SandboxService.webhook_test(data)
    except IntegrationError as exc:
        return _error(exc)
