import hashlib
import secrets
import uuid
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.statuses import (
    CREDENTIAL_ACTIVE,
    CREDENTIAL_REVOKED,
    DEFAULT_PARTNER_VERIFICATION_ITEMS,
    PARTNER_ACTIVE,
    PARTNER_APPROVABLE_STATUSES,
    PARTNER_APPROVED,
    PARTNER_ARCHIVED,
    PARTNER_DRAFT,
    PARTNER_PENDING,
    PARTNER_REJECTABLE_STATUSES,
    PARTNER_REJECTED,
    PARTNER_SUBMITTED,
    PARTNER_SUSPENDED,
    PARTNER_UNDER_REVIEW,
    VALID_CREDENTIAL_STATUSES,
    VALID_PARTNER_API_STATUSES,
    VALID_PARTNER_STATUSES,
    VALID_PARTNER_TYPES,
    VALID_PARTNER_USER_ROLES,
    VALID_PARTNER_USER_STATUSES,
    VALID_VERIFICATION_STATUSES,
    VERIFICATION_MISSING,
    VERIFICATION_REJECTED,
    VERIFICATION_SUBMITTED,
    VERIFICATION_VERIFIED,
)
from app.extensions.db import db
from app.models.partner import Partner
from app.models.partner_api_credential import PartnerApiCredential
from app.models.partner_service import PartnerService
from app.models.partner_user import PartnerUser
from app.models.partner_verification_item import PartnerVerificationItem


class PartnerPlatformError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class PartnerPlatformService:

    @staticmethod
    def _hash_secret(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_partner_code(partner_type):
        prefix = partner_type[:3].upper()
        count = Partner.query.filter(
            Partner.partner_type == partner_type
        ).count()
        return f"PTR-{prefix}-{count + 1:04d}"

    @staticmethod
    def _get_partner_or_raise(partner_id):
        partner = Partner.query.get(partner_id)
        if not partner:
            raise PartnerPlatformError("Partner not found", 404)
        return partner

    @staticmethod
    def _validate_partner_type(partner_type):
        if partner_type not in VALID_PARTNER_TYPES:
            raise PartnerPlatformError(
                f"Invalid partner_type. Must be one of: {', '.join(VALID_PARTNER_TYPES)}"
            )

    @staticmethod
    def _validate_api_status(api_status):
        if api_status not in VALID_PARTNER_API_STATUSES:
            raise PartnerPlatformError(
                f"Invalid api_status. Must be one of: {', '.join(VALID_PARTNER_API_STATUSES)}"
            )

    @staticmethod
    def _validate_status(status):
        if status not in VALID_PARTNER_STATUSES:
            raise PartnerPlatformError(
                f"Invalid status. Must be one of: {', '.join(VALID_PARTNER_STATUSES)}"
            )

    @staticmethod
    def _seed_verification_checklist(partner_id):
        for item_type in DEFAULT_PARTNER_VERIFICATION_ITEMS:
            db.session.add(
                PartnerVerificationItem(
                    partner_id=partner_id,
                    item_type=item_type,
                    status=VERIFICATION_MISSING,
                )
            )

    @staticmethod
    def _log_workflow_change(
        partner,
        action,
        event_type,
        message,
        actor_email="SYSTEM",
        ip_address="",
        severity="INFO",
    ):
        write_audit(
            action=action,
            object_type="Partner",
            object_id=partner.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type=event_type,
            object_type="Partner",
            object_id=partner.id,
            message=message,
            severity=severity,
        )

    @staticmethod
    def _transition_status(
        partner,
        new_status,
        action,
        event_type,
        message,
        actor_email="SYSTEM",
        ip_address="",
        severity="INFO",
    ):
        old_status = partner.status
        partner.status = new_status
        partner.updated_at = datetime.utcnow()
        PartnerPlatformService._log_workflow_change(
            partner,
            action=action,
            event_type=event_type,
            message=f"{message} ({old_status} -> {new_status})",
            actor_email=actor_email,
            ip_address=ip_address,
            severity=severity,
        )

    @staticmethod
    def create_partner(data, actor_email="SYSTEM", ip_address=""):
        partner_type = data.get("partner_type")
        legal_name = data.get("legal_name")
        display_name = data.get("display_name")

        if not partner_type or not legal_name or not display_name:
            raise PartnerPlatformError(
                "partner_type, legal_name, and display_name are required"
            )

        PartnerPlatformService._validate_partner_type(partner_type)

        api_status = data.get("api_status", "OFFLINE")
        PartnerPlatformService._validate_api_status(api_status)

        partner_code = data.get("partner_code") or PartnerPlatformService._generate_partner_code(
            partner_type
        )

        status = data.get("status", PARTNER_DRAFT)
        PartnerPlatformService._validate_status(status)

        partner = Partner(
            partner_code=partner_code,
            partner_type=partner_type,
            legal_name=legal_name,
            display_name=display_name,
            tax_code=data.get("tax_code"),
            license_number=data.get("license_number"),
            representative_name=data.get("representative_name"),
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address"),
            city=data.get("city"),
            province=data.get("province"),
            district=data.get("district"),
            status=status,
            verification_note=data.get("verification_note"),
            api_status=api_status,
            average_result_time_hours=data.get("average_result_time_hours"),
            pickup_sla_minutes=data.get("pickup_sla_minutes"),
            response_sla_minutes=data.get("response_sla_minutes"),
            working_hours_summary=data.get("working_hours_summary"),
            rating=data.get("rating", 0.0),
            review_count=data.get("review_count", 0),
            completed_orders=data.get("completed_orders", 0),
        )

        try:
            db.session.add(partner)
            db.session.flush()
            PartnerPlatformService._seed_verification_checklist(partner.id)
            write_event(
                event_type="PARTNER_CREATED",
                object_type="Partner",
                object_id=partner.id,
                message=f"Partner {partner.partner_code} created ({partner.partner_type})",
            )
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise PartnerPlatformError("Partner code already exists", 409)

        return partner

    @staticmethod
    def list_partners(partner_type=None, status=None):
        query = Partner.query

        if partner_type:
            query = query.filter(Partner.partner_type == partner_type)

        if status:
            query = query.filter(Partner.status == status)

        return query.order_by(Partner.created_at.desc()).all()

    @staticmethod
    def get_partner(partner_id):
        return PartnerPlatformService._get_partner_or_raise(partner_id)

    @staticmethod
    def get_partner_detail(partner_id):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)
        return {
            "partner": partner.to_dict(),
            "verification_items": [
                item.to_dict()
                for item in PartnerPlatformService.list_verification_items(partner_id)
            ],
            "users": [
                user.to_dict()
                for user in PartnerPlatformService.list_partner_users(partner_id)
            ],
            "api_credentials": [
                credential.to_dict()
                for credential in PartnerPlatformService.list_api_credentials(partner_id)
            ],
        }

    @staticmethod
    def update_partner(partner_id, data, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if "partner_type" in data:
            PartnerPlatformService._validate_partner_type(data["partner_type"])
            partner.partner_type = data["partner_type"]

        if "api_status" in data:
            PartnerPlatformService._validate_api_status(data["api_status"])
            partner.api_status = data["api_status"]

        if "status" in data:
            PartnerPlatformService._validate_status(data["status"])
            partner.status = data["status"]

        for field in (
            "legal_name",
            "display_name",
            "tax_code",
            "license_number",
            "representative_name",
            "phone",
            "email",
            "address",
            "city",
            "province",
            "district",
            "verification_note",
            "average_result_time_hours",
            "pickup_sla_minutes",
            "response_sla_minutes",
            "working_hours_summary",
            "rating",
            "review_count",
            "completed_orders",
        ):
            if field in data:
                setattr(partner, field, data[field])

        partner.updated_at = datetime.utcnow()
        db.session.commit()
        return partner

    @staticmethod
    def submit_partner(partner_id, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status not in (PARTNER_DRAFT, PARTNER_PENDING):
            raise PartnerPlatformError(
                f"Partner must be in DRAFT or PENDING to submit (current: {partner.status})",
                409,
            )

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_SUBMITTED,
            action="PARTNER_SUBMITTED",
            event_type="PARTNER_SUBMITTED",
            message=f"Partner {partner.partner_code} submitted for review",
            actor_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return partner

    @staticmethod
    def start_review(partner_id, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status not in (PARTNER_SUBMITTED, PARTNER_PENDING):
            raise PartnerPlatformError(
                f"Partner must be SUBMITTED or PENDING to review (current: {partner.status})",
                409,
            )

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_UNDER_REVIEW,
            action="PARTNER_UNDER_REVIEW",
            event_type="PARTNER_UNDER_REVIEW",
            message=f"Partner {partner.partner_code} moved under review",
            actor_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return partner

    @staticmethod
    def approve_partner(partner_id, verification_note=None, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status == PARTNER_APPROVED:
            raise PartnerPlatformError("Partner is already approved", 409)

        if partner.status not in PARTNER_APPROVABLE_STATUSES:
            raise PartnerPlatformError(
                f"Partner cannot be approved from status {partner.status}",
                409,
            )

        if verification_note:
            partner.verification_note = verification_note

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_APPROVED,
            action="PARTNER_APPROVED",
            event_type="PARTNER_APPROVED",
            message=f"Partner {partner.partner_code} approved",
            actor_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return partner

    @staticmethod
    def reject_partner(partner_id, verification_note=None, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status == PARTNER_REJECTED:
            raise PartnerPlatformError("Partner is already rejected", 409)

        if partner.status not in PARTNER_REJECTABLE_STATUSES:
            raise PartnerPlatformError(
                f"Partner cannot be rejected from status {partner.status}",
                409,
            )

        if verification_note:
            partner.verification_note = verification_note

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_REJECTED,
            action="PARTNER_REJECTED",
            event_type="PARTNER_REJECTED",
            message=f"Partner {partner.partner_code} rejected",
            actor_email=actor_email,
            ip_address=ip_address,
            severity="WARNING",
        )
        db.session.commit()
        return partner

    @staticmethod
    def activate_partner(partner_id, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status != PARTNER_APPROVED:
            raise PartnerPlatformError(
                f"Partner must be APPROVED to activate (current: {partner.status})",
                409,
            )

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_ACTIVE,
            action="PARTNER_ACTIVATED",
            event_type="PARTNER_ACTIVATED",
            message=f"Partner {partner.partner_code} activated",
            actor_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return partner

    @staticmethod
    def suspend_partner(partner_id, verification_note=None, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status == PARTNER_SUSPENDED:
            raise PartnerPlatformError("Partner is already suspended", 409)

        if verification_note:
            partner.verification_note = verification_note

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_SUSPENDED,
            action="PARTNER_SUSPENDED",
            event_type="PARTNER_SUSPENDED",
            message=f"Partner {partner.partner_code} suspended",
            actor_email=actor_email,
            ip_address=ip_address,
            severity="WARNING",
        )
        db.session.commit()
        return partner

    @staticmethod
    def archive_partner(partner_id, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        if partner.status == PARTNER_ARCHIVED:
            raise PartnerPlatformError("Partner is already archived", 409)

        PartnerPlatformService._transition_status(
            partner,
            PARTNER_ARCHIVED,
            action="PARTNER_ARCHIVED",
            event_type="PARTNER_ARCHIVED",
            message=f"Partner {partner.partner_code} archived",
            actor_email=actor_email,
            ip_address=ip_address,
        )
        db.session.commit()
        return partner

    @staticmethod
    def add_partner_user(partner_id, data):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        role = data.get("role")
        if role not in VALID_PARTNER_USER_ROLES:
            raise PartnerPlatformError(
                f"Invalid role. Must be one of: {', '.join(VALID_PARTNER_USER_ROLES)}"
            )

        user_id = data.get("user_id")
        email = data.get("email")
        if not user_id and not email:
            raise PartnerPlatformError("user_id or email is required")

        status = data.get("status", "INVITED")
        if status not in VALID_PARTNER_USER_STATUSES:
            raise PartnerPlatformError(
                f"Invalid status. Must be one of: {', '.join(VALID_PARTNER_USER_STATUSES)}"
            )

        user = PartnerUser(
            partner_id=partner.id,
            user_id=user_id,
            email=email,
            role=role,
            status=status,
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def list_partner_users(partner_id):
        PartnerPlatformService._get_partner_or_raise(partner_id)
        return PartnerUser.query.filter_by(partner_id=partner_id).order_by(
            PartnerUser.created_at.desc()
        ).all()

    @staticmethod
    def list_verification_items(partner_id):
        PartnerPlatformService._get_partner_or_raise(partner_id)
        return PartnerVerificationItem.query.filter_by(partner_id=partner_id).order_by(
            PartnerVerificationItem.item_type
        ).all()

    @staticmethod
    def update_verification_item(partner_id, item_id, data, actor_email="SYSTEM", ip_address=""):
        PartnerPlatformService._get_partner_or_raise(partner_id)

        item = PartnerVerificationItem.query.filter_by(
            id=item_id,
            partner_id=partner_id,
        ).first()
        if not item:
            raise PartnerPlatformError("Verification item not found", 404)

        if "status" in data:
            if data["status"] not in VALID_VERIFICATION_STATUSES:
                raise PartnerPlatformError(
                    f"Invalid status. Must be one of: {', '.join(VALID_VERIFICATION_STATUSES)}"
                )
            item.status = data["status"]

            if item.status == VERIFICATION_VERIFIED:
                item.verified_by = data.get("verified_by", actor_email)
                item.verified_at = datetime.utcnow()
            elif item.status in (VERIFICATION_MISSING, VERIFICATION_SUBMITTED, VERIFICATION_REJECTED):
                if "verified_by" in data:
                    item.verified_by = data.get("verified_by")
                if item.status != VERIFICATION_VERIFIED:
                    item.verified_at = None

        if "note" in data:
            item.note = data["note"]

        item.updated_at = datetime.utcnow()

        write_audit(
            action="PARTNER_VERIFICATION_UPDATED",
            object_type="PartnerVerificationItem",
            object_id=item.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="PARTNER_VERIFICATION_UPDATED",
            object_type="PartnerVerificationItem",
            object_id=item.id,
            message=f"Verification item {item.item_type} updated to {item.status}",
        )
        db.session.commit()
        return item

    @staticmethod
    def create_api_credential(partner_id, actor_email="SYSTEM", ip_address=""):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        client_id = f"ptr_{uuid.uuid4().hex[:16]}"
        client_secret = secrets.token_urlsafe(32)
        api_key = secrets.token_urlsafe(32)

        credential = PartnerApiCredential(
            partner_id=partner.id,
            client_id=client_id,
            client_secret_hash=PartnerPlatformService._hash_secret(client_secret),
            api_key_hash=PartnerPlatformService._hash_secret(api_key),
            status=CREDENTIAL_ACTIVE,
        )

        db.session.add(credential)
        db.session.flush()
        write_audit(
            action="PARTNER_API_CREDENTIAL_CREATED",
            object_type="PartnerApiCredential",
            object_id=credential.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="PARTNER_API_CREDENTIAL_CREATED",
            object_type="PartnerApiCredential",
            object_id=credential.id,
            message=f"API credential created for partner {partner.partner_code}",
        )
        db.session.commit()

        response = credential.to_dict()
        response["client_secret"] = client_secret
        response["api_key"] = api_key
        return response

    @staticmethod
    def list_api_credentials(partner_id):
        PartnerPlatformService._get_partner_or_raise(partner_id)
        return PartnerApiCredential.query.filter_by(partner_id=partner_id).order_by(
            PartnerApiCredential.created_at.desc()
        ).all()

    @staticmethod
    def revoke_api_credential(partner_id, credential_id, actor_email="SYSTEM", ip_address=""):
        PartnerPlatformService._get_partner_or_raise(partner_id)

        credential = PartnerApiCredential.query.filter_by(
            id=credential_id,
            partner_id=partner_id,
        ).first()
        if not credential:
            raise PartnerPlatformError("API credential not found", 404)

        if credential.status == CREDENTIAL_REVOKED:
            raise PartnerPlatformError("API credential is already revoked", 409)

        credential.status = CREDENTIAL_REVOKED
        credential.revoked_at = datetime.utcnow()

        write_audit(
            action="PARTNER_API_CREDENTIAL_REVOKED",
            object_type="PartnerApiCredential",
            object_id=credential.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="PARTNER_API_CREDENTIAL_REVOKED",
            object_type="PartnerApiCredential",
            object_id=credential.id,
            message=f"API credential {credential.client_id} revoked",
            severity="WARNING",
        )
        db.session.commit()
        return credential

    @staticmethod
    def add_partner_service(partner_id, data):
        partner = PartnerPlatformService._get_partner_or_raise(partner_id)

        service_code = data.get("service_code")
        service_name = data.get("service_name")

        if not service_code or not service_name:
            raise PartnerPlatformError("service_code and service_name are required")

        existing = PartnerService.query.filter_by(
            partner_id=partner.id,
            service_code=service_code,
        ).first()
        if existing:
            raise PartnerPlatformError("Service code already exists for this partner", 409)

        service = PartnerService(
            partner_id=partner.id,
            service_code=service_code,
            service_name=service_name,
            catalog_item_code=data.get("catalog_item_code"),
            description=data.get("description"),
            status=data.get("status", "ACTIVE"),
            average_result_time_hours=data.get("average_result_time_hours"),
        )

        db.session.add(service)
        db.session.commit()
        return service

    @staticmethod
    def list_partner_services(partner_id):
        PartnerPlatformService._get_partner_or_raise(partner_id)
        return PartnerService.query.filter_by(partner_id=partner_id).order_by(
            PartnerService.service_name
        ).all()
