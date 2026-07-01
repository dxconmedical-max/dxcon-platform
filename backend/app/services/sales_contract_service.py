from datetime import datetime, timedelta

from app.core.pagination import paginate_query, pagination_payload
from app.core.statuses import CRM_CONTRACT_ACTIVE, CRM_CONTRACT_TYPES
from app.extensions.db import db
from app.models.crm_sales_contract import SalesContract, SalesContractPrice
from app.services.crm_helpers import generate_code, get_or_404, list_resource, parse_date, parse_datetime


class SalesContractError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class SalesContractService:
    @staticmethod
    def list_contracts(
        page=1,
        per_page=20,
        status=None,
        contract_type=None,
        customer_id=None,
        organization_id=None,
        owner=None,
        q=None,
    ):
        filters = {
            "status": status,
            "contract_type": contract_type,
            "customer_id": customer_id,
            "organization_id": organization_id,
            "owner": owner,
            "q": q,
        }
        return list_resource(
            SalesContract,
            lambda item: item.to_dict(),
            search_fields=["contract_code", "title", "notes", "owner"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_contract(data):
        contract_type = data.get("contract_type")
        if contract_type not in CRM_CONTRACT_TYPES:
            raise SalesContractError(
                f"contract_type must be one of: {', '.join(CRM_CONTRACT_TYPES)}"
            )
        effective_date = parse_date(data.get("effective_date")) or datetime.utcnow().date()
        expiry_date = parse_date(data.get("expiry_date")) or (
            effective_date + timedelta(days=365)
        )
        renewal_reminder_at = parse_datetime(data.get("renewal_reminder_at"))
        if not renewal_reminder_at:
            reminder_date = expiry_date - timedelta(days=30)
            renewal_reminder_at = datetime.combine(reminder_date, datetime.min.time())

        contract = SalesContract(
            contract_code=data.get("contract_code") or generate_code("SC"),
            title=data["title"],
            contract_type=contract_type,
            customer_id=data.get("customer_id"),
            organization_id=data.get("organization_id"),
            effective_date=effective_date,
            expiry_date=expiry_date,
            renewal_reminder_at=renewal_reminder_at,
            corporate_discount_percent=float(data.get("corporate_discount_percent") or 0),
            status=data.get("status", CRM_CONTRACT_ACTIVE),
            notes=data.get("notes"),
            owner=data.get("owner"),
        )
        db.session.add(contract)
        db.session.flush()

        for price_data in data.get("prices") or []:
            price = SalesContractPrice(
                contract_id=contract.id,
                test_catalog_id=price_data.get("test_catalog_id"),
                item_code=price_data.get("item_code"),
                item_name=price_data.get("item_name", "Item"),
                standard_price=float(price_data.get("standard_price") or 0),
                contract_price=float(price_data.get("contract_price") or 0),
                discount_percent=float(price_data.get("discount_percent") or 0),
            )
            db.session.add(price)

        db.session.commit()
        return contract

    @staticmethod
    def get_contract(contract_id):
        contract = get_or_404(SalesContract, contract_id, SalesContractError)
        prices = SalesContractPrice.query.filter_by(contract_id=contract.id).all()
        payload = contract.to_dict()
        payload["prices"] = [price.to_dict() for price in prices]
        return payload

    @staticmethod
    def update_contract(contract_id, data):
        contract = get_or_404(SalesContract, contract_id, SalesContractError)
        for field in (
            "title",
            "contract_type",
            "customer_id",
            "organization_id",
            "status",
            "notes",
            "owner",
        ):
            if field in data:
                setattr(contract, field, data[field])
        if "corporate_discount_percent" in data:
            contract.corporate_discount_percent = float(data["corporate_discount_percent"] or 0)
        if "effective_date" in data:
            contract.effective_date = parse_date(data.get("effective_date"))
        if "expiry_date" in data:
            contract.expiry_date = parse_date(data.get("expiry_date"))
        if "renewal_reminder_at" in data:
            contract.renewal_reminder_at = parse_datetime(data.get("renewal_reminder_at"))
        contract.updated_at = datetime.utcnow()
        db.session.commit()
        return contract

    @staticmethod
    def delete_contract(contract_id):
        contract = get_or_404(SalesContract, contract_id, SalesContractError)
        SalesContractPrice.query.filter_by(contract_id=contract.id).delete()
        db.session.delete(contract)
        db.session.commit()

    @staticmethod
    def expiring_contracts(within_days=30):
        cutoff = datetime.utcnow().date() + timedelta(days=within_days)
        contracts = (
            SalesContract.query.filter(
                SalesContract.status == CRM_CONTRACT_ACTIVE,
                SalesContract.expiry_date <= cutoff,
            )
            .order_by(SalesContract.expiry_date.asc())
            .limit(20)
            .all()
        )
        return [contract.to_dict() for contract in contracts]

    @staticmethod
    def contracts_due_renewal():
        now = datetime.utcnow()
        contracts = (
            SalesContract.query.filter(
                SalesContract.status == CRM_CONTRACT_ACTIVE,
                SalesContract.renewal_reminder_at <= now,
            )
            .order_by(SalesContract.renewal_reminder_at.asc())
            .limit(20)
            .all()
        )
        return [contract.to_dict() for contract in contracts]
