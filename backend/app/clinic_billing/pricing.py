"""Apply a clinic's negotiated prices to a freshly created order. Never blocks ordering."""

from __future__ import annotations

import logging

from app.clinic_billing.logic import clinic_unit_price
from app.extensions.db import db

log = logging.getLogger(__name__)


def _reprice(order_code: str | None, organization_id: str | None) -> bool:
    """Re-price the order's lines with the clinic's price list / default discount.

    Runs inside a savepoint: if the billing tables are not migrated yet (or anything fails) the order keeps its
    catalog prices and ordering continues. Returns True when at least one line was re-priced.
    """
    if not order_code or not organization_id:
        return False
    try:
        with db.session.begin_nested():
            from app.business_engine.service import _recalc_order_totals
            from app.models.biz_order import BizInvoice, BizOrder, BizOrderItem
            from app.models.clinic_billing import ClinicBillingSetting, ClinicPrice

            order = BizOrder.query.filter_by(order_code=order_code).first()
            if order is None:
                return False
            setting = db.session.get(ClinicBillingSetting, organization_id)
            pct = setting.default_discount_pct if setting else 0.0
            prices = {p.test_catalog_id: p.price for p in ClinicPrice.query.filter_by(organization_id=organization_id)}
            if not prices and not pct:
                return False
            changed = False
            for item in BizOrderItem.query.filter_by(order_id=order.id).all():
                base = item.unit_price or 0
                new = clinic_unit_price(base, prices.get(item.test_catalog_id), pct)
                if new != base:
                    item.unit_price = new
                    item.line_total = round(new * (item.quantity or 1), 2)
                    changed = True
            if changed:
                db.session.flush()
                _recalc_order_totals(order)
                for inv in BizInvoice.query.filter_by(order_id=order.id).all():
                    inv.amount = order.total_amount
                db.session.flush()
            return changed
    except Exception:  # pragma: no cover - defensive: pricing must never block an order
        log.exception("apply_clinic_prices failed for %s", order_code)
        return False


def apply_clinic_prices(order_code: str | None, organization_id: str | None) -> bool:
    """Re-price the order for its clinic, then assign it to its lab (giá nhập). Both steps are non-blocking."""
    changed = _reprice(order_code, organization_id)
    from app.lab_payables.cost import auto_assign_lab

    auto_assign_lab(order_code, organization_id)
    return changed
