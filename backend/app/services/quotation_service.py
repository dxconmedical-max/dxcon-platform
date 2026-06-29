from datetime import datetime, timedelta

from app.core.pagination import paginate_query, pagination_payload
from app.core.statuses import (
    CRM_APPROVAL_APPROVED,
    CRM_APPROVAL_DRAFT,
    CRM_APPROVAL_PENDING,
    CRM_APPROVAL_REJECTED,
    CRM_PRICE_SOURCE_CATALOG,
    CRM_PRICE_SOURCE_CONTRACT,
    CRM_PRICE_SOURCE_CUSTOMER,
    CRM_QUOTATION_DRAFT,
)
from app.extensions.db import db
from app.models.crm_organization import Customer
from app.models.crm_quotation import DiscountRule, PriceBook, Quotation, QuotationItem
from app.models.crm_sales_contract import SalesContract, SalesContractPrice
from app.models.test_catalog import TestCatalog
from app.services.crm_helpers import generate_code, get_or_404, list_resource, parse_date


class QuotationError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class QuotationService:
    @staticmethod
    def list_quotations(
        page=1,
        per_page=20,
        approval_status=None,
        customer_id=None,
        opportunity_id=None,
        owner=None,
        q=None,
    ):
        filters = {
            "approval_status": approval_status,
            "customer_id": customer_id,
            "opportunity_id": opportunity_id,
            "owner": owner,
            "q": q,
        }
        return list_resource(
            Quotation,
            lambda item: item.to_dict(),
            search_fields=["quotation_code", "notes", "owner"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def _resolve_unit_price(test, customer_id=None, contract_id=None, source=CRM_PRICE_SOURCE_CATALOG):
        if source == CRM_PRICE_SOURCE_CONTRACT and contract_id:
            contract_price = SalesContractPrice.query.filter_by(
                contract_id=contract_id,
                test_catalog_id=test.id,
            ).first()
            if contract_price:
                return contract_price.contract_price, contract_price.discount_percent
            contract = SalesContract.query.get(contract_id)
            if contract:
                discount = contract.corporate_discount_percent or 0
                return test.price * (1 - discount / 100), discount

        if source == CRM_PRICE_SOURCE_CUSTOMER and customer_id:
            price_book = PriceBook.query.filter_by(
                customer_id=customer_id,
                test_catalog_id=test.id,
                source_type=CRM_PRICE_SOURCE_CUSTOMER,
                is_active=True,
            ).first()
            if price_book:
                return price_book.unit_price, price_book.discount_percent

        return test.price, 0

    @staticmethod
    def generate_quotation(data):
        customer_id = data.get("customer_id")
        if not customer_id:
            raise QuotationError("customer_id is required")
        get_or_404(Customer, customer_id, QuotationError)

        source = data.get("price_source", CRM_PRICE_SOURCE_CATALOG)
        contract_id = data.get("contract_id")
        test_ids = data.get("test_catalog_ids") or []
        if not test_ids:
            tests = TestCatalog.query.limit(5).all()
        else:
            tests = TestCatalog.query.filter(TestCatalog.id.in_(test_ids)).all()
        if not tests:
            raise QuotationError("No test catalog items available", 404)

        quotation = Quotation(
            quotation_code=data.get("quotation_code") or generate_code("QT"),
            customer_id=customer_id,
            opportunity_id=data.get("opportunity_id"),
            price_source=source,
            approval_status=CRM_QUOTATION_DRAFT,
            currency=data.get("currency", "VND"),
            valid_until=parse_date(data.get("valid_until"))
            or (datetime.utcnow() + timedelta(days=30)).date(),
            notes=data.get("notes"),
            owner=data.get("owner"),
        )
        db.session.add(quotation)
        db.session.flush()

        subtotal = 0
        discount_total = 0
        for test in tests:
            unit_price, discount_percent = QuotationService._resolve_unit_price(
                test,
                customer_id=customer_id,
                contract_id=contract_id,
                source=source,
            )
            quantity = 1
            line_total = unit_price * quantity
            subtotal += line_total
            discount_total += line_total * (discount_percent / 100)
            item = QuotationItem(
                quotation_id=quotation.id,
                test_catalog_id=test.id,
                item_code=test.code,
                item_name=test.name,
                quantity=quantity,
                unit_price=unit_price,
                discount_percent=discount_percent,
                line_total=line_total,
            )
            db.session.add(item)

        quotation.subtotal = subtotal
        quotation.discount_amount = discount_total
        quotation.total_amount = subtotal - discount_total
        db.session.commit()
        return quotation

    @staticmethod
    def create_quotation(data):
        if data.get("generate") or data.get("test_catalog_ids"):
            return QuotationService.generate_quotation(data)
        quotation = Quotation(
            quotation_code=data.get("quotation_code") or generate_code("QT"),
            customer_id=data.get("customer_id"),
            opportunity_id=data.get("opportunity_id"),
            price_source=data.get("price_source", CRM_PRICE_SOURCE_CATALOG),
            approval_status=data.get("approval_status", CRM_QUOTATION_DRAFT),
            subtotal=float(data.get("subtotal") or 0),
            discount_amount=float(data.get("discount_amount") or 0),
            total_amount=float(data.get("total_amount") or 0),
            currency=data.get("currency", "VND"),
            valid_until=parse_date(data.get("valid_until")),
            notes=data.get("notes"),
            owner=data.get("owner"),
        )
        db.session.add(quotation)
        db.session.commit()
        return quotation

    @staticmethod
    def get_quotation(quotation_id):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        items = QuotationItem.query.filter_by(quotation_id=quotation.id).all()
        payload = quotation.to_dict()
        payload["items"] = [item.to_dict() for item in items]
        return payload

    @staticmethod
    def update_quotation(quotation_id, data):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        for field in (
            "customer_id",
            "opportunity_id",
            "price_source",
            "approval_status",
            "currency",
            "notes",
            "owner",
        ):
            if field in data:
                setattr(quotation, field, data[field])
        for field in ("subtotal", "discount_amount", "total_amount"):
            if field in data:
                setattr(quotation, field, float(data[field] or 0))
        if "valid_until" in data:
            quotation.valid_until = parse_date(data.get("valid_until"))
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        return quotation

    @staticmethod
    def delete_quotation(quotation_id):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        QuotationItem.query.filter_by(quotation_id=quotation.id).delete()
        db.session.delete(quotation)
        db.session.commit()

    @staticmethod
    def submit_for_approval(quotation_id):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        quotation.approval_status = CRM_APPROVAL_PENDING
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        return quotation

    @staticmethod
    def approve_quotation(quotation_id):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        quotation.approval_status = CRM_APPROVAL_APPROVED
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        return quotation

    @staticmethod
    def reject_quotation(quotation_id):
        quotation = get_or_404(Quotation, quotation_id, QuotationError)
        quotation.approval_status = CRM_APPROVAL_REJECTED
        quotation.updated_at = datetime.utcnow()
        db.session.commit()
        return quotation

    @staticmethod
    def list_price_books(page=1, per_page=20, customer_id=None, source_type=None):
        query = PriceBook.query
        if customer_id:
            query = query.filter(PriceBook.customer_id == customer_id)
        if source_type:
            query = query.filter(PriceBook.source_type == source_type)
        query = query.order_by(PriceBook.created_at.desc())
        result = paginate_query(query, page=page, per_page=per_page)
        return pagination_payload(result["items"], result["pagination"], serializer=lambda p: p.to_dict())

    @staticmethod
    def create_price_book(data):
        price_book = PriceBook(
            price_book_code=data.get("price_book_code") or generate_code("PB"),
            name=data["name"],
            source_type=data.get("source_type", CRM_PRICE_SOURCE_CATALOG),
            customer_id=data.get("customer_id"),
            contract_id=data.get("contract_id"),
            test_catalog_id=data.get("test_catalog_id"),
            unit_price=float(data.get("unit_price") or 0),
            discount_percent=float(data.get("discount_percent") or 0),
            currency=data.get("currency", "VND"),
            is_active=bool(data.get("is_active", True)),
        )
        db.session.add(price_book)
        db.session.commit()
        return price_book

    @staticmethod
    def create_discount_rule(data):
        rule = DiscountRule(
            rule_code=data.get("rule_code") or generate_code("DISC"),
            name=data["name"],
            discount_percent=float(data.get("discount_percent") or 0),
            min_amount=float(data.get("min_amount") or 0),
            customer_id=data.get("customer_id"),
            contract_id=data.get("contract_id"),
            is_active=bool(data.get("is_active", True)),
        )
        db.session.add(rule)
        db.session.commit()
        return rule
