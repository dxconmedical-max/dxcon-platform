"""Patient Marketplace API routes — Epic 5."""

from __future__ import annotations

import os

from flask import Blueprint, request

from app.core.authenticated_identity import (
    blueprint_require_authenticated_user_except,
    get_authenticated_identity,
)
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
blueprint_require_authenticated_user_except(
    patient_marketplace_bp,
    public_exact=(
        "/api/v1/marketplace/v2/health",
        "/api/v1/marketplace/v2/payments/webhook",
    ),
    public_prefixes=("/api/v1/marketplace/catalog/",),
)


def _org_id():
    """Membership-validated org. Returns str or error response tuple."""
    from app.core.tenant_authorization import (
        AuthorizedTenant,
        client_requested_organization_id,
        resolve_authorized_tenant,
    )

    tenant = resolve_authorized_tenant(
        requested_organization_id=client_requested_organization_id(),
        require_scope=True,
    )
    if not isinstance(tenant, AuthorizedTenant):
        return tenant
    org = tenant.organization_id
    if not org:
        return {"error": "organization required", "code": "ORG_REQUIRED"}, 400
    return org


def _user_id() -> str | None:
    identity = get_authenticated_identity()
    return identity.user_id if identity else None


def _require_org():
    org = _org_id()
    if isinstance(org, str):
        return org, None
    return None, org


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
    org, err = _require_org()
    if err:
        return err
    try:
        return BookingService.create_booking(data, org, patient_user_id=_user_id()), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/bookings/<booking_id>/confirm", methods=["POST"])
def confirm_booking_v2(booking_id):
    org, err = _require_org()
    if err:
        return err
    try:
        return BookingService.confirm_booking(booking_id, org, actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/bookings/<booking_id>/cancel", methods=["POST"])
def cancel_booking_v2(booking_id):
    data = request.get_json(silent=True) or {}
    org, err = _require_org()
    if err:
        return err
    try:
        return BookingService.cancel_booking(booking_id, org, data.get("reason", ""), actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/payments/qr", methods=["POST"])
def create_qr_payment():
    data = request.get_json(silent=True) or {}
    org, err = _require_org()
    if err:
        return err
    try:
        return PaymentService.create_qr_payment(data["booking_id"], org, actor=_user_id()), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/payments/<payment_reference>/status", methods=["GET"])
def payment_status(payment_reference):
    org, err = _require_org()
    if err:
        return err
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
    org, err = _require_org()
    if err:
        return err
    return CatalogService.create_listing(data, org, actor=_user_id()), 201


@patient_marketplace_bp.route("/v2/listings/<listing_id>/approve", methods=["POST"])
def approve_listing(listing_id):
    org, err = _require_org()
    if err:
        return err
    try:
        return CatalogService.approve_listing(listing_id, org, actor=_user_id())
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/reviews", methods=["POST"])
def submit_review():
    data = request.get_json(silent=True) or {}
    org, err = _require_org()
    if err:
        return err
    user = _user_id()
    if not user:
        return {"error": "auth required", "code": "AUTH_REQUIRED"}, 401
    try:
        return ReviewService.submit_review(data, org, user), 201
    except MarketplaceError as exc:
        return {"error": exc.message, "code": exc.code}, exc.status_code


@patient_marketplace_bp.route("/v2/health", methods=["GET"])
def marketplace_health():
    return {"status": "OK", "module": "patient_marketplace", "epic": "5"}
