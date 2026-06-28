from flask import Blueprint, request

from app.services.partner_platform import PartnerPlatformError, PartnerPlatformService


partners_bp = Blueprint(
    "partners",
    __name__,
    url_prefix="/api/v1/partners",
)


def _client_ip():
    return request.remote_addr or ""


def _actor_email():
    return request.headers.get("X-User-Email", "SYSTEM")


@partners_bp.route("", methods=["GET"])
def list_partners():
    partner_type = request.args.get("partner_type")
    status = request.args.get("status")

    partners = PartnerPlatformService.list_partners(
        partner_type=partner_type,
        status=status,
    )

    return {
        "count": len(partners),
        "partners": [partner.to_dict() for partner in partners],
    }


@partners_bp.route("", methods=["POST"])
def create_partner():
    data = request.get_json(silent=True) or {}

    try:
        partner = PartnerPlatformService.create_partner(
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner created successfully",
        "partner": partner.to_dict(),
    }, 201


@partners_bp.route("/<partner_id>", methods=["GET"])
def get_partner(partner_id):
    detail = request.args.get("detail", "").lower() in ("1", "true", "yes")

    try:
        if detail:
            payload = PartnerPlatformService.get_partner_detail(partner_id)
        else:
            payload = PartnerPlatformService.get_partner(partner_id).to_dict()
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return payload


@partners_bp.route("/<partner_id>", methods=["PUT"])
def update_partner(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        partner = PartnerPlatformService.update_partner(
            partner_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner updated successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/submit", methods=["POST"])
def submit_partner(partner_id):
    try:
        partner = PartnerPlatformService.submit_partner(
            partner_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner submitted successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/review", methods=["POST"])
def review_partner(partner_id):
    try:
        partner = PartnerPlatformService.start_review(
            partner_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner moved to under review",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/approve", methods=["POST"])
def approve_partner(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        partner = PartnerPlatformService.approve_partner(
            partner_id,
            verification_note=data.get("verification_note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner approved successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/reject", methods=["POST"])
def reject_partner(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        partner = PartnerPlatformService.reject_partner(
            partner_id,
            verification_note=data.get("verification_note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner rejected successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/activate", methods=["POST"])
def activate_partner(partner_id):
    try:
        partner = PartnerPlatformService.activate_partner(
            partner_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner activated successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/suspend", methods=["POST"])
def suspend_partner(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        partner = PartnerPlatformService.suspend_partner(
            partner_id,
            verification_note=data.get("verification_note"),
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner suspended successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/archive", methods=["POST"])
def archive_partner(partner_id):
    try:
        partner = PartnerPlatformService.archive_partner(
            partner_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner archived successfully",
        "partner": partner.to_dict(),
    }


@partners_bp.route("/<partner_id>/users", methods=["GET"])
def list_partner_users(partner_id):
    try:
        users = PartnerPlatformService.list_partner_users(partner_id)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(users),
        "users": [user.to_dict() for user in users],
    }


@partners_bp.route("/<partner_id>/users", methods=["POST"])
def add_partner_user(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        user = PartnerPlatformService.add_partner_user(partner_id, data)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner user created successfully",
        "user": user.to_dict(),
    }, 201


@partners_bp.route("/<partner_id>/verification", methods=["GET"])
def list_verification_items(partner_id):
    try:
        items = PartnerPlatformService.list_verification_items(partner_id)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(items),
        "items": [item.to_dict() for item in items],
    }


@partners_bp.route("/<partner_id>/verification/<item_id>", methods=["PUT"])
def update_verification_item(partner_id, item_id):
    data = request.get_json(silent=True) or {}

    try:
        item = PartnerPlatformService.update_verification_item(
            partner_id,
            item_id,
            data,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Verification item updated successfully",
        "item": item.to_dict(),
    }


@partners_bp.route("/<partner_id>/credentials", methods=["GET"])
def list_api_credentials(partner_id):
    try:
        credentials = PartnerPlatformService.list_api_credentials(partner_id)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(credentials),
        "credentials": [credential.to_dict() for credential in credentials],
    }


@partners_bp.route("/<partner_id>/credentials", methods=["POST"])
def create_api_credential(partner_id):
    try:
        credential = PartnerPlatformService.create_api_credential(
            partner_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "API credential created successfully",
        "credential": credential,
    }, 201


@partners_bp.route("/<partner_id>/credentials/<credential_id>/revoke", methods=["POST"])
def revoke_api_credential(partner_id, credential_id):
    try:
        credential = PartnerPlatformService.revoke_api_credential(
            partner_id,
            credential_id,
            actor_email=_actor_email(),
            ip_address=_client_ip(),
        )
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "API credential revoked successfully",
        "credential": credential.to_dict(),
    }


@partners_bp.route("/<partner_id>/services", methods=["GET"])
def list_partner_services(partner_id):
    try:
        services = PartnerPlatformService.list_partner_services(partner_id)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "count": len(services),
        "services": [service.to_dict() for service in services],
    }


@partners_bp.route("/<partner_id>/services", methods=["POST"])
def add_partner_service(partner_id):
    data = request.get_json(silent=True) or {}

    try:
        service = PartnerPlatformService.add_partner_service(partner_id, data)
    except PartnerPlatformError as exc:
        return {"error": exc.message}, exc.status_code

    return {
        "message": "Partner service created successfully",
        "service": service.to_dict(),
    }, 201
