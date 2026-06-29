import json
import uuid
from datetime import datetime

from app.core.audit import write_audit
from app.core.statuses import (
    ATTACHMENT_TYPE_IMAGE,
    ATTACHMENT_TYPE_PDF,
    LAB_RESULT_APPROVED,
    LAB_RESULT_DRAFT,
    LAB_RESULT_IN_REVIEW,
    LAB_RESULT_RELEASED,
    LAB_RESULT_REJECTED,
    LAB_RESULT_TRANSITIONS,
    LAB_RESULT_VALIDATED,
    MEDICAL_ORDER_REPORT_READY,
    RESULT_REVIEW_APPROVED,
    RESULT_REVIEW_REJECTED,
    RESULT_REVIEW_SUBMITTED,
    RESULT_SOURCE_ANALYZER,
    RESULT_SOURCE_MANUAL,
    RESULT_TIMELINE_APPROVED,
    RESULT_TIMELINE_RELEASED,
    RESULT_TIMELINE_REJECTED,
    RESULT_TIMELINE_REVIEWED,
    RESULT_TIMELINE_UPLOADED,
    RESULT_TIMELINE_VALIDATED,
)
from app.extensions.db import db
from app.models.lab_result import LabResult
from app.models.lab_result_item import LabResultItem
from app.models.medical_order import MedicalOrder
from app.models.result_attachment import ResultAttachment
from app.models.result_release import ResultRelease
from app.models.result_review import ResultReview
from app.models.result_timeline import ResultTimeline
from app.services.order_workflow_service import OrderWorkflowService
from app.services.result_flag import calculate_result_flag


class ResultGatewayError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ResultGatewayBase:

    @staticmethod
    def _get_result_or_raise(result_id):
        result = LabResult.query.get(result_id)
        if not result:
            raise ResultGatewayError("Lab result not found", 404)
        return result

    @staticmethod
    def _ensure_editable(result):
        if result.is_locked or result.status == LAB_RESULT_RELEASED:
            raise ResultGatewayError("Released result is immutable", 409)

    @staticmethod
    def _generate_result_code():
        count = LabResult.query.count()
        return f"LR-{count + 1:06d}"

    @staticmethod
    def _generate_release_code():
        count = ResultRelease.query.count()
        return f"REL-{count + 1:06d}"

    @staticmethod
    def _can_transition(result, target_status):
        allowed = LAB_RESULT_TRANSITIONS.get(result.status, [])
        return target_status in allowed

    @staticmethod
    def _transition(result, target_status):
        if not ResultGatewayBase._can_transition(result, target_status):
            raise ResultGatewayError(
                f"Cannot transition from {result.status} to {target_status}",
                409,
            )
        previous = result.status
        result.status = target_status
        result.updated_at = datetime.utcnow()
        return previous, target_status

    @staticmethod
    def _write_timeline(
        result,
        event_type,
        message=None,
        from_status=None,
        to_status=None,
        actor_email="SYSTEM",
        metadata=None,
    ):
        entry = ResultTimeline(
            lab_result_id=result.id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            message=message,
            actor_email=actor_email,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(entry)
        return entry

    @staticmethod
    def _resolve_order(medical_order_id):
        order = MedicalOrder.query.get(medical_order_id)
        if not order:
            raise ResultGatewayError("Medical order not found", 404)
        return order

    @staticmethod
    def _create_items(result, items):
        created = []
        for index, item in enumerate(items or []):
            if not item.get("test_name") and not item.get("test_code"):
                continue
            flag = item.get("flag")
            if not flag:
                flag = calculate_result_flag(
                    item.get("result_value"),
                    item.get("reference_range"),
                )
            row = LabResultItem(
                lab_result_id=result.id,
                test_code=item.get("test_code"),
                test_name=item.get("test_name") or item.get("test_code"),
                result_value=item.get("result_value"),
                unit=item.get("unit"),
                reference_range=item.get("reference_range"),
                flag=flag or "UNKNOWN",
                sequence=item.get("sequence", index),
            )
            db.session.add(row)
            created.append(row)
        return created

    @staticmethod
    def _create_attachments(result, attachments, actor_email="SYSTEM"):
        created = []
        for attachment in attachments or []:
            file_name = attachment.get("file_name")
            file_path = attachment.get("file_path")
            if not file_name or not file_path:
                continue
            mime_type = attachment.get("mime_type", "")
            attachment_type = attachment.get("attachment_type")
            if not attachment_type:
                lowered = file_name.lower()
                if lowered.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    attachment_type = ATTACHMENT_TYPE_IMAGE
                else:
                    attachment_type = ATTACHMENT_TYPE_PDF
            row = ResultAttachment(
                lab_result_id=result.id,
                file_name=file_name,
                file_path=file_path,
                mime_type=mime_type,
                attachment_type=attachment_type,
                uploaded_by=actor_email,
            )
            db.session.add(row)
            created.append(row)
        return created

    @staticmethod
    def get_result_detail(result_id):
        result = ResultGatewayBase._get_result_or_raise(result_id)
        payload = result.to_dict(include_items=True, include_attachments=True)
        payload["reviews"] = [
            review.to_dict()
            for review in ResultReview.query.filter_by(lab_result_id=result.id)
            .order_by(ResultReview.created_at.desc())
            .all()
        ]
        release = (
            ResultRelease.query.filter_by(lab_result_id=result.id)
            .order_by(ResultRelease.released_at.desc())
            .first()
        )
        payload["release"] = release.to_dict() if release else None
        return payload

    @staticmethod
    def list_results(status=None, medical_order_id=None):
        query = LabResult.query
        if status:
            query = query.filter(LabResult.status == status)
        if medical_order_id:
            query = query.filter(LabResult.medical_order_id == medical_order_id)
        return query.order_by(LabResult.created_at.desc()).all()

    @staticmethod
    def get_timeline(result_id):
        ResultGatewayBase._get_result_or_raise(result_id)
        return (
            ResultTimeline.query.filter_by(lab_result_id=result_id)
            .order_by(ResultTimeline.created_at.asc())
            .all()
        )


class ResultUploadService(ResultGatewayBase):

    @staticmethod
    def upload_analyzer(data, actor_email="SYSTEM", ip_address=""):
        medical_order_id = data.get("medical_order_id")
        if not medical_order_id:
            raise ResultGatewayError("medical_order_id is required", 400)

        order = ResultUploadService._resolve_order(medical_order_id)
        analyzer_payload = data.get("analyzer_payload") or data.get("payload") or {}
        items = data.get("items") or analyzer_payload.get("items") or []

        result = LabResult(
            result_code=ResultUploadService._generate_result_code(),
            medical_order_id=order.id,
            partner_id=order.partner_id,
            patient_id=order.patient_id,
            patient_name=order.patient_name,
            source_type=RESULT_SOURCE_ANALYZER,
            status=LAB_RESULT_DRAFT,
            analyzer_payload_json=json.dumps(analyzer_payload),
            summary=data.get("summary"),
        )
        db.session.add(result)
        db.session.flush()

        ResultUploadService._create_items(result, items)
        ResultUploadService._create_attachments(
            result,
            data.get("attachments"),
            actor_email=actor_email,
        )
        ResultUploadService._write_timeline(
            result,
            RESULT_TIMELINE_UPLOADED,
            message="Analyzer result uploaded",
            to_status=LAB_RESULT_DRAFT,
            actor_email=actor_email,
            metadata={"source_type": RESULT_SOURCE_ANALYZER},
        )
        write_audit("RESULT_UPLOAD", "LabResult", result.id, actor_email, ip_address)
        db.session.commit()
        return result

    @staticmethod
    def create_manual(data, actor_email="SYSTEM", ip_address=""):
        medical_order_id = data.get("medical_order_id")
        if not medical_order_id:
            raise ResultGatewayError("medical_order_id is required", 400)

        order = ResultUploadService._resolve_order(medical_order_id)
        items = data.get("items") or []
        if not items:
            raise ResultGatewayError("At least one result item is required", 400)

        result = LabResult(
            result_code=ResultUploadService._generate_result_code(),
            medical_order_id=order.id,
            partner_id=order.partner_id,
            patient_id=order.patient_id,
            patient_name=order.patient_name,
            source_type=RESULT_SOURCE_MANUAL,
            status=LAB_RESULT_DRAFT,
            summary=data.get("summary"),
        )
        db.session.add(result)
        db.session.flush()

        ResultUploadService._create_items(result, items)
        ResultUploadService._create_attachments(
            result,
            data.get("attachments"),
            actor_email=actor_email,
        )
        ResultUploadService._write_timeline(
            result,
            RESULT_TIMELINE_UPLOADED,
            message="Manual result entered",
            to_status=LAB_RESULT_DRAFT,
            actor_email=actor_email,
            metadata={"source_type": RESULT_SOURCE_MANUAL},
        )
        write_audit("RESULT_MANUAL", "LabResult", result.id, actor_email, ip_address)
        db.session.commit()
        return result


class ResultValidationService(ResultGatewayBase):

    @staticmethod
    def validate(result_id, actor_email="SYSTEM", ip_address=""):
        result = ResultValidationService._get_result_or_raise(result_id)
        ResultValidationService._ensure_editable(result)

        if not result.items:
            raise ResultGatewayError("Result has no items to validate", 400)

        invalid_items = [
            item.id
            for item in result.items
            if not item.test_name or item.result_value in (None, "")
        ]
        if invalid_items:
            raise ResultGatewayError("All result items must have test name and value", 400)

        previous, target = ResultValidationService._transition(result, LAB_RESULT_VALIDATED)
        ResultValidationService._write_timeline(
            result,
            RESULT_TIMELINE_VALIDATED,
            message="Result validated",
            from_status=previous,
            to_status=target,
            actor_email=actor_email,
        )
        write_audit("RESULT_VALIDATE", "LabResult", result.id, actor_email, ip_address)
        db.session.commit()
        return result


class ResultReviewService(ResultGatewayBase):

    @staticmethod
    def submit_review(result_id, data, actor_email="SYSTEM", ip_address=""):
        result = ResultReviewService._get_result_or_raise(result_id)
        ResultReviewService._ensure_editable(result)

        if result.status not in (LAB_RESULT_VALIDATED, LAB_RESULT_REJECTED):
            raise ResultGatewayError("Result must be validated before review", 409)

        reviewer_email = data.get("reviewer_email") or actor_email
        review = ResultReview(
            lab_result_id=result.id,
            reviewer_email=reviewer_email,
            review_status=RESULT_REVIEW_SUBMITTED,
            comments=data.get("comments"),
        )
        db.session.add(review)

        previous, target = ResultReviewService._transition(result, LAB_RESULT_IN_REVIEW)
        ResultReviewService._write_timeline(
            result,
            RESULT_TIMELINE_REVIEWED,
            message=data.get("comments") or "Result submitted for review",
            from_status=previous,
            to_status=target,
            actor_email=reviewer_email,
        )
        write_audit("RESULT_REVIEW", "LabResult", result.id, reviewer_email, ip_address)
        db.session.commit()
        return result, review


class ResultApprovalService(ResultGatewayBase):

    @staticmethod
    def approve(result_id, data, actor_email="SYSTEM", ip_address=""):
        result = ResultApprovalService._get_result_or_raise(result_id)
        ResultApprovalService._ensure_editable(result)

        if result.status != LAB_RESULT_IN_REVIEW:
            raise ResultGatewayError("Result must be in review before approval", 409)

        approver_email = data.get("approver_email") or actor_email
        review = (
            ResultReview.query.filter_by(lab_result_id=result.id)
            .order_by(ResultReview.created_at.desc())
            .first()
        )
        if review:
            review.review_status = RESULT_REVIEW_APPROVED
            if data.get("comments"):
                review.comments = data.get("comments")

        previous, target = ResultApprovalService._transition(result, LAB_RESULT_APPROVED)
        ResultApprovalService._write_timeline(
            result,
            RESULT_TIMELINE_APPROVED,
            message=data.get("comments") or "Result approved",
            from_status=previous,
            to_status=target,
            actor_email=approver_email,
        )
        write_audit("RESULT_APPROVE", "LabResult", result.id, approver_email, ip_address)
        db.session.commit()
        return result

    @staticmethod
    def reject(result_id, data, actor_email="SYSTEM", ip_address=""):
        result = ResultApprovalService._get_result_or_raise(result_id)
        ResultApprovalService._ensure_editable(result)

        if result.status not in (LAB_RESULT_IN_REVIEW, LAB_RESULT_VALIDATED):
            raise ResultGatewayError("Result cannot be rejected in current status", 409)

        reviewer_email = data.get("reviewer_email") or actor_email
        review = ResultReview(
            lab_result_id=result.id,
            reviewer_email=reviewer_email,
            review_status=RESULT_REVIEW_REJECTED,
            comments=data.get("comments"),
        )
        db.session.add(review)

        previous, target = ResultApprovalService._transition(result, LAB_RESULT_REJECTED)
        ResultApprovalService._write_timeline(
            result,
            RESULT_TIMELINE_REJECTED,
            message=data.get("comments") or "Result rejected",
            from_status=previous,
            to_status=target,
            actor_email=reviewer_email,
        )
        write_audit("RESULT_REJECT", "LabResult", result.id, reviewer_email, ip_address)
        db.session.commit()
        return result


class ResultReleaseService(ResultGatewayBase):

    @staticmethod
    def _build_release_payload(result):
        return {
            "result_code": result.result_code,
            "medical_order_id": result.medical_order_id,
            "partner_id": result.partner_id,
            "patient_id": result.patient_id,
            "patient_name": result.patient_name,
            "source_type": result.source_type,
            "status": LAB_RESULT_RELEASED,
            "version": result.version,
            "summary": result.summary,
            "items": [item.to_dict() for item in result.items],
            "attachments": [item.to_dict() for item in result.attachments],
            "released_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def release(result_id, data, actor_email="SYSTEM", ip_address=""):
        result = ResultReleaseService._get_result_or_raise(result_id)

        if result.status != LAB_RESULT_APPROVED:
            raise ResultGatewayError("Result must be approved before release", 409)

        if result.is_locked:
            raise ResultGatewayError("Result already released", 409)

        payload = ResultReleaseService._build_release_payload(result)
        release = ResultRelease(
            lab_result_id=result.id,
            release_code=ResultReleaseService._generate_release_code(),
            released_by=data.get("released_by") or actor_email,
            release_channel=data.get("release_channel", "PORTAL"),
            payload_json=json.dumps(payload),
            version=result.version,
        )
        db.session.add(release)

        previous, target = ResultReleaseService._transition(result, LAB_RESULT_RELEASED)
        result.is_locked = True
        result.released_version = result.version
        result.released_at = datetime.utcnow()

        ResultReleaseService._write_timeline(
            result,
            RESULT_TIMELINE_RELEASED,
            message=data.get("comments") or "Result released to patient/doctor",
            from_status=previous,
            to_status=target,
            actor_email=actor_email,
            metadata={"release_code": release.release_code},
        )
        write_audit("RESULT_RELEASE", "LabResult", result.id, actor_email, ip_address)

        order = MedicalOrder.query.get(result.medical_order_id)
        if order:
            try:
                OrderWorkflowService.transition(
                    order.id,
                    MEDICAL_ORDER_REPORT_READY,
                    actor_email=actor_email,
                    ip_address=ip_address,
                    message=f"Lab result {result.result_code} released",
                )
            except Exception:
                pass

        db.session.commit()
        return result, release
