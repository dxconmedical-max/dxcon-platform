"""Payment provider adapters — Epic 5."""

from __future__ import annotations

import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any


class PaymentProviderAdapter(ABC):
    provider_code: str = "BASE"
    production_ready: bool = False

    @abstractmethod
    def create_payment(self, amount: float, currency: str, reference: str, metadata: dict | None = None) -> dict[str, Any]:
        ...

    def create_qr(self, amount: float, currency: str, reference: str) -> dict[str, Any]:
        return self.create_payment(amount, currency, reference)

    def query_status(self, payment_reference: str) -> dict[str, Any]:
        return {"status": "PENDING", "payment_reference": payment_reference}

    def handle_webhook(self, payload: dict, headers: dict | None = None) -> dict[str, Any]:
        return {"status": payload.get("status", "PENDING")}

    def verify_signature(self, payload: dict, signature: str, secret: str) -> bool:
        return False

    def cancel_payment(self, payment_reference: str) -> dict[str, Any]:
        return {"status": "CANCELLED", "payment_reference": payment_reference}

    def refund_payment(self, payment_reference: str, amount: float, reason: str | None = None) -> dict[str, Any]:
        return {"status": "REFUND_PENDING", "payment_reference": payment_reference, "amount": amount}

    def reconcile(self, date: str) -> dict[str, Any]:
        return {"date": date, "matched": 0, "unmatched": 0}


class ManualBankQRAdapter(PaymentProviderAdapter):
    provider_code = "MANUAL_BANK_QR"
    production_ready = True

    def create_payment(self, amount: float, currency: str, reference: str, metadata: dict | None = None) -> dict[str, Any]:
        expires = datetime.utcnow() + timedelta(minutes=15)
        return {
            "provider": self.provider_code,
            "payment_reference": reference,
            "amount": amount,
            "currency": currency,
            "status": "PENDING",
            "qr_payload": f"DXCON|{reference}|{amount}|VND",
            "expires_at": expires.isoformat(),
            "production_ready": True,
        }

    def query_status(self, payment_reference: str) -> dict[str, Any]:
        return {"provider": self.provider_code, "payment_reference": payment_reference, "status": "PENDING"}


class MockPaymentAdapter(PaymentProviderAdapter):
    """Test-only — never used in production runtime."""

    provider_code = "MOCK_TEST"
    production_ready = False

    def create_payment(self, amount: float, currency: str, reference: str, metadata: dict | None = None) -> dict[str, Any]:
        return {
            "provider": self.provider_code,
            "payment_reference": reference or f"MOCK-{uuid.uuid4().hex[:8]}",
            "amount": amount,
            "status": "PENDING",
            "test_only": True,
        }


class VNPayPlaceholderAdapter(PaymentProviderAdapter):
    provider_code = "VNPAY"
    production_ready = False

    def create_payment(self, amount: float, currency: str, reference: str, metadata: dict | None = None) -> dict[str, Any]:
        return {
            "provider": self.provider_code,
            "configured": False,
            "foundation_only": True,
            "message": "VNPay adapter not configured for production",
        }


ADAPTER_REGISTRY: dict[str, type[PaymentProviderAdapter]] = {
    "MANUAL_BANK_QR": ManualBankQRAdapter,
    "MOCK_TEST": MockPaymentAdapter,
    "VNPAY": VNPayPlaceholderAdapter,
}

_STRICT_ENVS = {"production", "prod", "live", "staging", "stage", "uat"}


def get_payment_adapter(provider_code: str) -> PaymentProviderAdapter:
    cls = ADAPTER_REGISTRY.get(provider_code.upper(), ManualBankQRAdapter)
    env = os.getenv("APP_ENV", "development").strip().lower()
    if env in _STRICT_ENVS and not cls.production_ready:
        # Production guard: the test-only adapter must never settle real payments.
        raise ValueError(
            f"Payment provider '{provider_code}' is not production-ready "
            f"and is disabled in {env} environments"
        )
    return cls()
