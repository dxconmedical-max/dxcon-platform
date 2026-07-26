"""Reception Payment Engine — validation, state, history over Business Engine.

Reuses ``app.business_engine.service`` for order/invoice/payment persistence.
Does not duplicate pricing or order creation.
"""

from __future__ import annotations

from typing import Any

from app.business_engine import service as biz
from app.business_engine.statuses import ORDER_PAID, ORDER_PAYMENT_PENDING
from app.models.biz_order import BizOrder, BizPayment
from app.reception_workspace.errors import ReceptionWorkspaceError

# Canonical tenders. ``transfer`` is bank transfer.
PAYMENT_METHODS = ("cash", "transfer", "qr", "pos", "corporate", "insurance")

# Accepted aliases → canonical method stored on BizPayment.
PAYMENT_METHOD_ALIASES = {
    "bank_transfer": "transfer",
    "bank": "transfer",
    "cash_payment": "cash",
}

PAYMENT_SUMMARY_STATUSES = ("unpaid", "partial", "paid")

# Payment engine feature flags
PARTIAL_PAYMENTS_SUPPORTED = True

# Logical payment desk states (derived; BizPayment has no status column).
PAYMENT_STATE_UNPAID = "unpaid"
PAYMENT_STATE_PARTIAL = "partial"
PAYMENT_STATE_PAID = "paid"
PAYMENT_STATE_NOT_PAYABLE = "not_payable"

PAYMENT_STATE_TRANSITIONS: dict[str, tuple[str, ...]] = {
    PAYMENT_STATE_UNPAID: (PAYMENT_STATE_PARTIAL, PAYMENT_STATE_PAID),
    PAYMENT_STATE_PARTIAL: (PAYMENT_STATE_PARTIAL, PAYMENT_STATE_PAID),
    PAYMENT_STATE_PAID: (),  # terminal for desk collect
}


def normalize_payment_method(payment_method: str) -> str:
    raw = (payment_method or "").strip().lower()
    if not raw:
        raise ReceptionWorkspaceError("payment_method is required")
    return PAYMENT_METHOD_ALIASES.get(raw, raw)


def validate_payment_method(payment_method: str) -> str:
    method = normalize_payment_method(payment_method)
    if method not in PAYMENT_METHODS:
        raise ReceptionWorkspaceError(f"Invalid payment method: {payment_method}")
    return method


def validate_payment_amount(
    amount: float | None,
    outstanding: float,
    *,
    allow_partial: bool = PARTIAL_PAYMENTS_SUPPORTED,
) -> float:
    outstanding = round(float(outstanding), 2)
    if amount is None:
        pay_amount = outstanding
    else:
        pay_amount = round(float(amount), 2)
    if pay_amount <= 0:
        raise ReceptionWorkspaceError("Payment amount must be greater than zero")
    if pay_amount > outstanding + 0.009:
        raise ReceptionWorkspaceError(
            f"Overpayment is not allowed (outstanding={outstanding})"
        )
    if not allow_partial and pay_amount < outstanding - 0.009:
        raise ReceptionWorkspaceError(
            "Partial payments are not supported. Collect the full outstanding amount."
        )
    return pay_amount


def payment_desk_state(order: BizOrder, *, outstanding: float, paid_amount: float) -> str:
    if order.status == ORDER_PAID or outstanding <= 0:
        return PAYMENT_STATE_PAID
    if paid_amount > 0:
        return PAYMENT_STATE_PARTIAL
    if order.status in {ORDER_PAYMENT_PENDING, "draft"}:
        return PAYMENT_STATE_UNPAID
    return PAYMENT_STATE_NOT_PAYABLE


def assert_payment_transition(from_state: str, to_state: str) -> None:
    allowed = PAYMENT_STATE_TRANSITIONS.get(from_state, ())
    if to_state not in allowed and from_state != to_state:
        raise ReceptionWorkspaceError(
            f"Invalid payment state transition: {from_state} → {to_state}"
        )


def list_payment_history(order: BizOrder) -> list[dict[str, Any]]:
    rows = (
        BizPayment.query.filter_by(order_id=order.id)
        .order_by(BizPayment.paid_at.asc(), BizPayment.created_at.asc())
        .all()
    )
    return [row.to_dict() for row in rows]


def build_payment_summary(order: BizOrder) -> dict[str, Any]:
    payments = BizPayment.query.filter_by(order_id=order.id).all()
    paid_amount = round(sum(float(p.amount or 0) for p in payments), 2)
    order_total = round(float(order.total_amount or 0), 2)
    outstanding_amount = round(max(0.0, order_total - paid_amount), 2)
    status = payment_desk_state(
        order, outstanding=outstanding_amount, paid_amount=paid_amount
    )
    if status == PAYMENT_STATE_NOT_PAYABLE:
        if paid_amount <= 0:
            status = PAYMENT_STATE_UNPAID
        elif outstanding_amount <= 0:
            status = PAYMENT_STATE_PAID
        else:
            status = PAYMENT_STATE_PARTIAL
    return {
        "order_total": order_total,
        "paid_amount": paid_amount,
        "outstanding_amount": outstanding_amount,
        "discount": round(float(order.discount or 0), 2),
        "subtotal": round(float(order.subtotal or 0), 2),
        "tax": None,
        "status": status,
        "payment_methods_supported": list(PAYMENT_METHODS),
        "partial_payments_supported": PARTIAL_PAYMENTS_SUPPORTED,
        "payment_count": len(payments),
    }


def resolve_order(order_ref: str) -> BizOrder:
    from sqlalchemy import or_

    order = BizOrder.query.filter(
        or_(BizOrder.order_code == order_ref, BizOrder.id == order_ref)
    ).first()
    if not order:
        raise ReceptionWorkspaceError("Order not found")
    return order


def record_payment(
    order_ref: str,
    *,
    payment_method: str,
    amount: float | None = None,
    receipt_number: str | None = None,
    actor: str | None = None,
) -> BizPayment:
    """Validate + record via Business Engine ``record_order_payment``."""
    method = validate_payment_method(payment_method)
    order = resolve_order(order_ref)
    summary = build_payment_summary(order)
    before = summary["status"]
    pay_amount = validate_payment_amount(
        amount,
        summary["outstanding_amount"],
        allow_partial=PARTIAL_PAYMENTS_SUPPORTED,
    )
    after = (
        PAYMENT_STATE_PAID
        if pay_amount + 0.009 >= summary["outstanding_amount"]
        else PAYMENT_STATE_PARTIAL
    )
    if before != PAYMENT_STATE_PAID:
        assert_payment_transition(before, after)
    return biz.record_order_payment(
        order_ref,
        payment_method=method,
        amount=pay_amount,
        receipt_number=receipt_number,
        actor=actor,
    )
