import hashlib
import hmac
import json

from flask import current_app


def sign_outbound_payload(secret, payload):
    payload_text = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True)
    return hmac.new(secret.encode(), payload_text.encode(), hashlib.sha256).hexdigest()


def verify_inbound_signature(secret, payload, signature):
    if not secret or not signature:
        return False
    expected = sign_outbound_payload(secret, payload)
    return hmac.compare_digest(expected, signature)


def sign_request_headers(secret, payload, headers=None):
    headers = dict(headers or {})
    signature = sign_outbound_payload(secret, payload)
    headers["X-DxCon-Signature"] = signature
    headers["X-DxCon-Signature-Algorithm"] = "HMAC-SHA256"
    return headers


def verify_request(secret, payload, headers):
    signature = headers.get("X-DxCon-Signature") or headers.get("X-Webhook-Signature")
    return verify_inbound_signature(secret or current_app.config.get("INTEGRATION_SIGNING_SECRET", ""), payload, signature)
