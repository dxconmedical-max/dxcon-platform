from datetime import datetime
import uuid

from app.extensions.db import db


class PriceBook(db.Model):
    __tablename__ = "crm_price_books"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    price_book_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    source_type = db.Column(db.String(50), default="CATALOG")
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    contract_id = db.Column(db.String(36), db.ForeignKey("crm_sales_contracts.id"))
    test_catalog_id = db.Column(db.String(36))
    unit_price = db.Column(db.Float, default=0)
    discount_percent = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default="VND")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "price_book_code": self.price_book_code,
            "name": self.name,
            "source_type": self.source_type,
            "customer_id": self.customer_id,
            "contract_id": self.contract_id,
            "test_catalog_id": self.test_catalog_id,
            "unit_price": self.unit_price,
            "discount_percent": self.discount_percent,
            "currency": self.currency,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DiscountRule(db.Model):
    __tablename__ = "crm_discount_rules"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    min_amount = db.Column(db.Float, default=0)
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    contract_id = db.Column(db.String(36), db.ForeignKey("crm_sales_contracts.id"))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "rule_code": self.rule_code,
            "name": self.name,
            "discount_percent": self.discount_percent,
            "min_amount": self.min_amount,
            "customer_id": self.customer_id,
            "contract_id": self.contract_id,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Quotation(db.Model):
    __tablename__ = "crm_quotations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quotation_code = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    opportunity_id = db.Column(db.String(36), db.ForeignKey("crm_opportunities.id"))
    price_source = db.Column(db.String(50), default="CATALOG")
    approval_status = db.Column(db.String(50), default="DRAFT")
    subtotal = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    currency = db.Column(db.String(10), default="VND")
    valid_until = db.Column(db.Date)
    notes = db.Column(db.Text)
    owner = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_code": self.quotation_code,
            "customer_id": self.customer_id,
            "opportunity_id": self.opportunity_id,
            "price_source": self.price_source,
            "approval_status": self.approval_status,
            "subtotal": self.subtotal,
            "discount_amount": self.discount_amount,
            "total_amount": self.total_amount,
            "currency": self.currency,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "notes": self.notes,
            "owner": self.owner,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class QuotationItem(db.Model):
    __tablename__ = "crm_quotation_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quotation_id = db.Column(
        db.String(36), db.ForeignKey("crm_quotations.id"), nullable=False
    )
    test_catalog_id = db.Column(db.String(36))
    item_code = db.Column(db.String(50))
    item_name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, default=0)
    discount_percent = db.Column(db.Float, default=0)
    line_total = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "quotation_id": self.quotation_id,
            "test_catalog_id": self.test_catalog_id,
            "item_code": self.item_code,
            "item_name": self.item_name,
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "discount_percent": self.discount_percent,
            "line_total": self.line_total,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
