"""Patient Marketplace API routes — Epic 5."""

from __future__ import annotations

import os

from flask import Blueprint, request

from app.patient_marketplace.home_collection import HomeCollectionService
from app.patient_marketplace.slot_engine import SlotEngineService
from app.patient_marketplace.service import (
    BookingService,
    CatalogService,
    ComparisonService,
    MarketplaceError,
    PaymentService,
    PricingService,
    ReviewService,
    SearchService,
)

patient_marketplace_bp = Blueprint("patient_marketplace", __name__, url_prefix="/api/v1/marketplace")


def _org_id() -> str | None:
    return request.headers.get("X-Organization-Id")


def _user_id() -> str | None:
    return request.headers.get("X-User-Id")


@patient_marketplace_bp.route("/public/services", methods=["GET"])
def public_services():
    return SearchService.list_services(
        q=request.args.get("q"),
        category=request.args.get("category"),
        city=request.args.get("city"),
        home_collection=request.args.get("home_collection", type=lambda v: v == "true"),
        min_price=request.args.get("min_price", type=float),
        max_price=request.args.get("max_price", type=float),
        featured=request.args.get("featured", type=lambda v: v == "true"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    )


@patient_marketplace_bp.route("/public/services/<listing_id>", methods=["GET"])
def public_service_detail(listing_id):
    try:
        return SearchService.get_listing(listing_id)
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/public/packages", methods=["GET"])
def public_packages():
    return SearchService.list_packages(
        q=request.args.get("q"),
        city=request.args.get("city"),
        home_collection=request.args.get("home_collection", type=lambda v: v == "true"),
        featured=request.args.get("featured", type=lambda v: v == "true"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    )


@patient_marketplace_bp.route("/public/packages/<listing_id>", methods=["GET"])
def public_package_detail(listing_id):
    try:
        return SearchService.get_listing(listing_id)
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/public/partners", methods=["GET"])
def public_partners():
    return SearchService.list_partners(
        q=request.args.get("q"),
        city=request.args.get("city"),
        provider_type=request.args.get("provider_type"),
        featured=request.args.get("featured", type=lambda v: v == "true"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    )


@patient_marketplace_bp.route("/public/partners/<provider_id>", methods=["GET"])
def public_partner_detail(provider_id):
    try:
        return SearchService.provider_profile(provider_id)
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/providers/<provider_id>/slots", methods=["GET"])
def provider_slots(provider_id):
    org = _org_id() or request.args.get("organization_id", "default-org")
    try:
        return SlotEngineService.list_available_slots(
            provider_id,
            organization_id=org,
            slot_date=request.args.get("date", ""),
            duration_minutes=request.args.get("duration", 30, type=int),
        )
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/slots/hold", methods=["POST"])
def hold_slot():
    data = request.get_json(silent=True) or {}
    org = _org_id() or data.get("organization_id", "default-org")
    try:
        from datetime import datetime
        start = datetime.fromisoformat(data["slot_start"])
        end = datetime.fromisoformat(data["slot_end"])
        return SlotEngineService.hold_slot(
            data["provider_id"],
            organization_id=org,
            slot_start=start,
            slot_end=end,
            patient_user_id=_user_id(),
        ), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/addresses", methods=["GET"])
def list_addresses():
    org = _org_id()
    user = _user_id()
    if not org or not user:
        return {"error": "auth required", "code": "AUTH_REQUIRED"}, 401
    return HomeCollectionService.list_addresses(user, organization_id=org)


@patient_marketplace_bp.route("/addresses", methods=["POST"])
def save_address():
    data = request.get_json(silent=True) or {}
    org = _org_id()
    user = _user_id()
    if not org or not user:
        return {"error": "auth required", "code": "AUTH_REQUIRED"}, 401
    return HomeCollectionService.save_address(data, organization_id=org, patient_user_id=user), 201


@patient_marketplace_bp.route("/catalog/quote-package", methods=["POST"])
def quote_package():
    data = request.get_json(silent=True) or {}
    try:
        return PricingService.quote_package(
            data["listing_id"],
            promotion_code=data.get("promotion_code"),
            distance_km=float(data.get("distance_km", 0)),
            urgent=bool(data.get("urgent")),
        )
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/catalog/search", methods=["GET"])
def search_catalog():
    return SearchService.search_listings(
        q=request.args.get("q"),
        city=request.args.get("city"),
        min_price=request.args.get("min_price", type=float),
        max_price=request.args.get("max_price", type=float),
        service_type=request.args.get("service_type"),
        home_collection=request.args.get("home_collection", type=lambda v: v == "true"),
        page=request.args.get("page", 1, type=int),
        per_page=request.args.get("per_page", 20, type=int),
    )


@patient_marketplace_bp.route("/catalog/providers/<provider_id>", methods=["GET"])
def provider_profile(provider_id):
    try:
        return SearchService.provider_profile(provider_id)
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/catalog/compare", methods=["POST"])
def compare_listings():
    data = request.get_json(silent=True) or {}
    try:
        return ComparisonService.compare_listings(
            data.get("listing_ids", []),
            patient_lat=data.get("lat"),
            patient_lng=data.get("lng"),
        )
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/catalog/quote", methods=["POST"])
def pricing_quote():
    data = request.get_json(silent=True) or {}
    try:
        return PricingService.quote(
            data["listing_id"],
            promotion_code=data.get("promotion_code"),
            distance_km=float(data.get("distance_km", 0)),
            urgent=bool(data.get("urgent")),
        )
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/catalog/serviceability", methods=["POST"])
def check_serviceability():
    data = request.get_json(silent=True) or {}
    return BookingService.check_serviceability(data["provider_id"], float(data["lat"]), float(data["lng"]))


@patient_marketplace_bp.route("/v2/bookings", methods=["POST"])
def create_booking_v2():
    data = request.get_json(silent=True) or {}
    org = _org_id() or data.get("organization_id")
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return BookingService.create_booking(data, org, patient_user_id=_user_id()), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/bookings/<booking_id>/confirm", methods=["POST"])
def confirm_booking_v2(booking_id):
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return BookingService.confirm_booking(booking_id, org, actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/bookings/<booking_id>/cancel", methods=["POST"])
def cancel_booking_v2(booking_id):
    data = request.get_json(silent=True) or {}
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return BookingService.cancel_booking(booking_id, org, data.get("reason", ""), actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/payments/qr", methods=["POST"])
def create_qr_payment():
    data = request.get_json(silent=True) or {}
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return PaymentService.create_qr_payment(data["booking_id"], org, actor=_user_id()), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/payments/<payment_reference>/status", methods=["GET"])
def payment_status(payment_reference):
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return PaymentService.payment_status(payment_reference, org)
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/payments/webhook", methods=["POST"])
def payment_webhook():
    data = request.get_json(silent=True) or {}
    signature = request.headers.get("X-Payment-Signature", "")
    secret = os.environ.get("MARKETPLACE_PAYMENT_WEBHOOK_SECRET", "dxcon-marketplace-webhook-dev")
    try:
        return PaymentService.handle_webhook(data, signature, secret)
    except MarketplaceError as exc:
        return {"error": "rejected", "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/listings", methods=["POST"])
def create_listing():
    data = request.get_json(silent=True) or {}
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    return CatalogService.create_listing(data, org, actor=_user_id()), 201


@patient_marketplace_bp.route("/v2/listings/<listing_id>/approve", methods=["POST"])
def approve_listing(listing_id):
    org = _org_id()
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    try:
        return CatalogService.approve_listing(listing_id, org, actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/reviews", methods=["POST"])
def submit_review():
    data = request.get_json(silent=True) or {}
    org = _org_id()
    user = _user_id()
    if not org or not user:
        return {"error": "auth required", "code": "AUTH_REQUIRED"}, 401
    try:
        return ReviewService.submit_review(data, org, user), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/health", methods=["GET"])
def marketplace_health():
    return {"status": "OK", "module": "patient_marketplace", "epic": "5"}
