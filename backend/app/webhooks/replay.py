import json
import secrets

from app.extensions.db import db
from app.services.integration_platform_service import IntegrationError, WebhookEngineService
from app.webhooks.models import WebhookReplayLog


class WebhookReplayService:
    @staticmethod
    def replay_delivery(delivery_id, replay_token=None, force=False):
        if replay_token:
            prior = WebhookReplayLog.query.filter_by(replay_token=replay_token).first()
            if prior and prior.delivery_id == delivery_id and prior.status == "COMPLETED" and not force:
                return {
                    "replay_safe": True,
                    "duplicate": True,
                    "delivery_id": delivery_id,
                    "result": json.loads(prior.detail_json or "{}"),
                }

        result = WebhookEngineService.replay_delivery(delivery_id)
        token = replay_token or secrets.token_hex(16)
        log = WebhookReplayLog(
            delivery_id=delivery_id,
            replay_token=token,
            status="COMPLETED",
            detail_json=json.dumps(result),
        )
        db.session.add(log)
        db.session.commit()
        return {"replay_safe": True, "duplicate": False, "replay_token": token, "result": result}

    @staticmethod
    def replay_from_payload(data):
        delivery_id = data.get("delivery_id")
        if not delivery_id:
            raise IntegrationError("delivery_id is required", 400)
        return WebhookReplayService.replay_delivery(
            delivery_id,
            replay_token=data.get("replay_token"),
            force=bool(data.get("force")),
        )
