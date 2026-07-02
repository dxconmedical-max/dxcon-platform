import json

from flask import current_app

from app.webhooks.signatures import sign_outbound_payload, sign_request_headers


class OutboundSigningService:
    @staticmethod
    def sign_payload(payload, secret=None):
        secret = secret or current_app.config.get("INTEGRATION_SIGNING_SECRET", "dxcon-integration-secret")
        payload_text = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
        return {
            "signature": sign_outbound_payload(secret, payload_text),
            "algorithm": "HMAC-SHA256",
            "payload": payload_text,
        }

    @staticmethod
    def signed_headers(payload, secret=None, headers=None):
        secret = secret or current_app.config.get("INTEGRATION_SIGNING_SECRET", "dxcon-integration-secret")
        payload_text = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
        return sign_request_headers(secret, payload_text, headers)
