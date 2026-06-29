from datetime import datetime
import uuid

from app.extensions.db import db


class SalesContract(db.Model):
    __tablename__ = "crm_sales_contracts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_code = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    contract_type = db.Column(db.String(50), nullable=False)
    customer_id = db.Column(db.String(36), db.ForeignKey("crm_customers.id"))
    organization_id = db.Column(db.String(36), db.ForeignKey("crm_organizations.id"))
    effective_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    renewal_reminder_at = db.Column(db.DateTime)
    corporate_discount_percent = db.Column(db.Float, default=0)
    status = db.Column(db.String(50), default="ACTIVE")
    notes = db.Column(db.Text)
    owner = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "contract_code": self.contract_code,
            "title": self.title,
            "contract_type": self.contract_type,
            "customer_id": self.customer_id,
            "organization_id": self.organization_id,
            "effective_date": (
                self.effective_date.isoformat() if self.effective_date else None
            ),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "renewal_reminder_at": (
                self.renewal_reminder_at.isoformat() if self.renewal_reminder_at else None
            ),
            "corporate_discount_percent": self.corporate_discount_percent,
            "status": self.status,
            "notes": self.notes,
            "owner": self.owner,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class SalesContractPrice(db.Model):
    __tablename__ = "crm_sales_contract_prices"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_id = db.Column(
        db.String(36), db.ForeignKey("crm_sales_contracts.id"), nullable=False
    )
    test_catalog_id = db.Column(db.String(36))
    item_code = db.Column(db.String(50))
    item_name = db.Column(db.String(255), nullable=False)
    standard_price = db.Column(db.Float, default=0)
    contract_price = db.Column(db.Float, default=0)
    discount_percent = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "contract_id": self.contract_id,
            "test_catalog_id": self.test_catalog_id,
            "item_code": self.item_code,
            "item_name": self.item_name,
            "standard_price": self.standard_price,
            "contract_price": self.contract_price,
            "discount_percent": self.discount_percent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
