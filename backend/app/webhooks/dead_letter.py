from app.core.statuses import INTEGRATION_WEBHOOK_DELIVERY_FAILED
from app.extensions.db import db
from app.models.integration_platform import WebhookDelivery
from app.services.integration_platform_service import IntegrationError, WebhookEngineService


class WebhookDeadLetterService:
    @staticmethod
    def can_retry(delivery):
        return delivery.attempt_count < delivery.max_retries

    @staticmethod
    def mark_failed(delivery_id, reason):
        delivery = WebhookDelivery.query.filter_by(id=delivery_id).first()
        if delivery is None:
            raise IntegrationError("Delivery not found", 404)
        delivery.status = INTEGRATION_WEBHOOK_DELIVERY_FAILED
        delivery.failure_reason = reason
        db.session.commit()
        return delivery.to_dict()

    @staticmethod
    def hardened_retry(delivery_id):
        delivery = WebhookDelivery.query.filter_by(id=delivery_id).first()
        if delivery is None:
            raise IntegrationError("Delivery not found", 404)
        if not WebhookDeadLetterService.can_retry(delivery):
            return WebhookDeadLetterService.mark_failed(delivery_id, "Maximum retries exceeded")
        return WebhookEngineService.retry_delivery(delivery_id)
