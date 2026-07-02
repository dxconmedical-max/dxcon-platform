import json

from app.extensions.db import db
from app.webhooks.models import WebhookIdempotencyKey


class WebhookIdempotencyService:
    @staticmethod
    def check_or_store(idempotency_key, webhook_id, delivery_id, response_payload):
        if not idempotency_key:
            return {"duplicate": False, "stored": False}

        existing = WebhookIdempotencyKey.query.filter_by(idempotency_key=idempotency_key).first()
        if existing:
            return {
                "duplicate": True,
                "stored": False,
                "delivery_id": existing.delivery_id,
                "response": json.loads(existing.response_json or "{}"),
            }

        row = WebhookIdempotencyKey(
            idempotency_key=idempotency_key,
            webhook_id=webhook_id,
            delivery_id=delivery_id,
            response_json=json.dumps(response_payload or {}),
        )
        db.session.add(row)
        db.session.commit()
        return {"duplicate": False, "stored": True, "delivery_id": delivery_id, "response": response_payload}
