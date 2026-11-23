"""Real MoMo one-time payment (captureWallet) client. Stdlib only.

Credentials come from environment variables set in Coolify, never from code:
MOMO_PARTNER_CODE, MOMO_ACCESS_KEY, MOMO_SECRET_KEY, MOMO_ENV (test | production).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request
import uuid

MIN_AMOUNT = 1_000
MAX_AMOUNT = 50_000_000

_HOSTS = {
    "test": "https://test-payment.momo.vn",
    "production": "https://payment.momo.vn",
}

_CREATE_FIELDS = ("accessKey", "amount", "extraData", "ipnUrl", "orderId", "orderInfo", "partnerCode", "redirectUrl", "requestId", "requestType")
_IPN_FIELDS = ("accessKey", "amount", "extraData", "message", "orderId", "orderInfo", "orderType", "partnerCode", "payType", "requestId", "responseTime", "resultCode", "transId")


class MoMoError(Exception):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _cfg() -> dict:
    return {
        "partner": os.environ.get("MOMO_PARTNER_CODE", "").strip(),
        "access": os.environ.get("MOMO_ACCESS_KEY", "").strip(),
        "secret": os.environ.get("MOMO_SECRET_KEY", "").strip(),
        "env": (os.environ.get("MOMO_ENV", "test").strip().lower() or "test"),
    }


def is_configured() -> bool:
    c = _cfg()
    return bool(c["partner"] and c["access"] and c["secret"])


def sign(fields: tuple[str, ...], data: dict, secret: str) -> str:
    raw = "&".join(f"{k}={data.get(k, '')}" for k in fields)
    return hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()


def momo_order_id(order_code: str) -> str:
    """Unique per attempt; the order code is recoverable with parse_order_code()."""
    return f"{order_code}_{uuid.uuid4().hex[:8]}"


def parse_order_code(momo_id: str) -> str | None:
    if not momo_id or "_" not in momo_id:
        return None
    return momo_id.rsplit("_", 1)[0] or None


def _post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=UTF-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 - fixed https hosts
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise MoMoError("Không kết nối được MoMo, thử lại sau.") from exc


def create_payment(*, order_code: str, amount: int, order_info: str, ipn_url: str, redirect_url: str) -> dict:
    c = _cfg()
    if not is_configured():
        raise MoMoError("MoMo chưa được cấu hình.", 503)
    if not (MIN_AMOUNT <= amount <= MAX_AMOUNT):
        raise MoMoError(f"MoMo chỉ nhận từ {MIN_AMOUNT:,} đến {MAX_AMOUNT:,} VND mỗi lần.", 400)
    host = _HOSTS.get(c["env"], _HOSTS["test"])
    body = {
        "partnerCode": c["partner"],
        "accessKey": c["access"],
        "requestId": uuid.uuid4().hex,
        "amount": str(amount),
        "orderId": momo_order_id(order_code),
        "orderInfo": order_info[:200],
        "redirectUrl": redirect_url,
        "ipnUrl": ipn_url,
        "requestType": "captureWallet",
        "extraData": "",
        "lang": "vi",
    }
    body["signature"] = sign(_CREATE_FIELDS, body, c["secret"])
    body.pop("accessKey")  # accessKey is only part of the signed string, not the request body
    data = _post(f"{host}/v2/gateway/api/create", body)
    if int(data.get("resultCode", -1)) != 0:
        raise MoMoError(f"MoMo từ chối: {data.get('message', 'lỗi không rõ')}", 502)
    return {
        "pay_url": data.get("payUrl"),
        "qr_code_url": data.get("qrCodeUrl"),
        "deeplink": data.get("deeplink"),
        "momo_order_id": body["orderId"],
        "amount": amount,
    }


def verify_ipn(payload: dict) -> bool:
    c = _cfg()
    if not is_configured():
        return False
    data = dict(payload)
    data["accessKey"] = c["access"]
    expected = sign(_IPN_FIELDS, data, c["secret"])
    return hmac.compare_digest(expected, str(payload.get("signature", "")))
