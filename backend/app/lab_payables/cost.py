"""Lab cost (giá nhập) per order and automatic lab routing. Never blocks ordering."""

from __future__ import annotations

import logging

from app.extensions.db import db

log = logging.getLogger(__name__)

DEFAULT_SCOPE = "DEFAULT"


def order_cost(order, lab_id: str) -> tuple[float, int]:
    """(cost_total, missing_count): sum of lab cost x quantity; lines the lab has no price for count as missing."""
    from app.models.lab_payables import LabCostPrice

    costs = {c.test_catalog_id: c.cost for c in LabCostPrice.query.filter_by(organization_id=lab_id)}
    total = 0.0
    missing = 0
    for item in order.items:
        cost = costs.get(item.test_catalog_id)
        if cost is None:
            missing += 1
            continue
        total += cost * (item.quantity or 1)
    return round(total, 2), missing


def assign_lab(order, lab_id: str, actor: str | None):
    """Create or refresh the order's lab assignment with current cost and sell totals."""
    from app.models.lab_payables import LabPayableLine, OrderLabCost

    cost, missing = order_cost(order, lab_id)
    row = OrderLabCost.query.filter_by(order_code=order.order_code).first()
    if row is not None and LabPayableLine.query.filter_by(order_code=order.order_code).first() is not None:
        return None  # already on a payable statement: frozen
    if row is None:
        row = OrderLabCost(order_code=order.order_code, lab_organization_id=lab_id)
        db.session.add(row)
    row.lab_organization_id = lab_id
    row.cost_total = cost
    row.sell_total = round(order.total_amount or 0, 2)
    row.missing_count = missing
    row.assigned_by = (actor or "")[:120] or None
    return row


def routed_lab(clinic_org_id: str | None) -> str | None:
    from app.models.lab_payables import LabRouting

    for scope in (clinic_org_id, DEFAULT_SCOPE):
        if not scope:
            continue
        row = db.session.get(LabRouting, scope)
        if row is not None:
            return row.lab_organization_id
    return None


def auto_assign_lab(order_code: str | None, clinic_org_id: str | None) -> bool:
    """Assign a new order to its routed lab (clinic setting, else default). Runs in a savepoint; silent on failure."""
    if not order_code:
        return False
    try:
        with db.session.begin_nested():
            from app.models.biz_order import BizOrder
            from app.models.lab_payables import OrderLabCost

            if OrderLabCost.query.filter_by(order_code=order_code).first() is not None:
                return False
            lab_id = routed_lab(clinic_org_id)
            if not lab_id:
                return False
            order = BizOrder.query.filter_by(order_code=order_code).first()
            if order is None:
                return False
            assign_lab(order, lab_id, "auto")
            db.session.flush()
            return True
    except Exception:  # pragma: no cover - defensive
        log.exception("auto_assign_lab failed for %s", order_code)
        return False
