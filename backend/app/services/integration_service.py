import json
import uuid
from datetime import datetime

from app.core.statuses import (
    HIS_PATIENT_SYNCED,
    INTEGRATION_CONNECTION_ACTIVE,
    INTEGRATION_MESSAGE_PROCESSED,
    INTEGRATION_MESSAGE_RECEIVED,
    INTEGRATION_PARTNER_ACTIVE,
    INTEGRATION_TYPE_HIS,
    INTEGRATION_TYPE_LIS,
    LIS_ORDER_ACCEPTED,
    LIS_RESULT_RELEASED,
)
from app.extensions.db import db
from app.models.his_patient_message import HISPatientMessage
from app.models.integration_audit_log import IntegrationAuditLog
from app.models.integration_connection import IntegrationConnection
from app.models.integration_message import IntegrationMessage
from app.models.integration_partner import IntegrationPartner
from app.models.lis_order_message import LISOrderMessage
from app.models.lis_result_message import LISResultMessage
from app.models.patient import Patient


class IntegrationError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class IntegrationParserService:

    @staticmethod
    def parse_payload(raw_payload):
        if isinstance(raw_payload, str):
            try:
                return json.loads(raw_payload)
            except json.JSONDecodeError:
                return {"raw": raw_payload}
        return raw_payload or {}


class IntegrationGatewayService:

    @staticmethod
    def _write_audit(action, connection_id=None, message_id=None, detail=None, actor_email="SYSTEM"):
        db.session.add(
            IntegrationAuditLog(
                connection_id=connection_id,
                message_id=message_id,
                action=action,
                detail=detail,
                actor_email=actor_email,
            )
        )

    @staticmethod
    def ensure_partner(data):
        partner = IntegrationPartner.query.filter_by(partner_code=data.get("partner_code")).first()
        if partner:
            return partner
        partner = IntegrationPartner(
            partner_code=data.get("partner_code") or f"INT-{IntegrationPartner.query.count() + 1:04d}",
            partner_name=data.get("partner_name") or "Integration Partner",
            integration_type=data.get("integration_type", INTEGRATION_TYPE_LIS),
            endpoint_url=data.get("endpoint_url"),
            status=INTEGRATION_PARTNER_ACTIVE,
        )
        db.session.add(partner)
        db.session.commit()
        return partner

    @staticmethod
    def list_connections(partner_id=None, status=None):
        query = IntegrationConnection.query
        if partner_id:
            query = query.filter_by(partner_id=partner_id)
        if status:
            query = query.filter_by(status=status)
        rows = query.order_by(IntegrationConnection.created_at.desc()).all()
        return {"count": len(rows), "connections": [row.to_dict() for row in rows]}

    @staticmethod
    def create_connection(data, actor_email="SYSTEM"):
        partner_id = data.get("partner_id")
        if not partner_id:
            partner = IntegrationGatewayService.ensure_partner(data)
            partner_id = partner.id
        partner = IntegrationPartner.query.get(partner_id)
        if not partner:
            raise IntegrationError("Integration partner not found", 404)

        connection = IntegrationConnection(
            connection_code=data.get("connection_code") or f"CONN-{IntegrationConnection.query.count() + 1:04d}",
            partner_id=partner_id,
            protocol=data.get("protocol", "HL7_FHIR"),
            auth_type=data.get("auth_type", "API_KEY"),
            config_json=json.dumps(data.get("config") or {}),
            status=data.get("status", INTEGRATION_CONNECTION_ACTIVE),
        )
        db.session.add(connection)
        IntegrationGatewayService._write_audit(
            "CONNECTION_CREATED",
            connection_id=connection.id,
            detail=f"Connection {connection.connection_code} created",
            actor_email=actor_email,
        )
        db.session.commit()
        return connection

    @staticmethod
    def _get_connection_or_raise(connection_id):
        connection = IntegrationConnection.query.get(connection_id)
        if not connection:
            raise IntegrationError("Integration connection not found", 404)
        return connection

    @staticmethod
    def _create_message(connection_id, message_type, payload, actor_email="SYSTEM"):
        message = IntegrationMessage(
            message_code=f"MSG-{IntegrationMessage.query.count() + 1:06d}",
            connection_id=connection_id,
            message_type=message_type,
            direction="INBOUND",
            payload_json=json.dumps(payload),
            status=INTEGRATION_MESSAGE_RECEIVED,
        )
        db.session.add(message)
        db.session.flush()
        IntegrationGatewayService._write_audit(
            "MESSAGE_RECEIVED",
            connection_id=connection_id,
            message_id=message.id,
            detail=message_type,
            actor_email=actor_email,
        )
        return message

    @staticmethod
    def list_messages(connection_id=None, message_type=None):
        query = IntegrationMessage.query
        if connection_id:
            query = query.filter_by(connection_id=connection_id)
        if message_type:
            query = query.filter_by(message_type=message_type)
        rows = query.order_by(IntegrationMessage.created_at.desc()).all()
        return {"count": len(rows), "messages": [row.to_dict() for row in rows]}

    @staticmethod
    def list_audit(connection_id=None, limit=100):
        query = IntegrationAuditLog.query
        if connection_id:
            query = query.filter_by(connection_id=connection_id)
        rows = query.order_by(IntegrationAuditLog.created_at.desc()).limit(limit).all()
        return {"count": len(rows), "audit": [row.to_dict() for row in rows]}


class IntegrationMessageRouter:

    @staticmethod
    def route(message_type, connection_id, payload, actor_email="SYSTEM"):
        if message_type == "LIS_ORDER":
            return LISOrderService.process_order(connection_id, payload, actor_email=actor_email)
        if message_type == "LIS_RESULT":
            return LISResultService.process_result(connection_id, payload, actor_email=actor_email)
        if message_type == "HIS_PATIENT":
            return HISPatientService.process_patient(connection_id, payload, actor_email=actor_email)
        raise IntegrationError(f"Unsupported message type: {message_type}", 400)


class LISOrderService:

    @staticmethod
    def process_order(connection_id, data, actor_email="SYSTEM"):
        IntegrationGatewayService._get_connection_or_raise(connection_id)
        payload = IntegrationParserService.parse_payload(data)
        external_order_id = payload.get("external_order_id") or payload.get("order_id")
        if not external_order_id:
            raise IntegrationError("external_order_id is required", 400)

        message = IntegrationGatewayService._create_message(connection_id, "LIS_ORDER", payload, actor_email)
        order_msg = LISOrderMessage(
            message_id=message.id,
            external_order_id=external_order_id,
            patient_code=payload.get("patient_code"),
            test_codes_json=json.dumps(payload.get("test_codes") or []),
            status=LIS_ORDER_ACCEPTED,
        )
        db.session.add(order_msg)
        message.status = INTEGRATION_MESSAGE_PROCESSED
        message.processed_at = datetime.utcnow()
        IntegrationGatewayService._write_audit(
            "LIS_ORDER_PROCESSED",
            connection_id=connection_id,
            message_id=message.id,
            detail=external_order_id,
            actor_email=actor_email,
        )
        db.session.commit()
        return {"message": message.to_dict(), "order": order_msg.to_dict()}


class LISResultService:

    @staticmethod
    def process_result(connection_id, data, actor_email="SYSTEM"):
        IntegrationGatewayService._get_connection_or_raise(connection_id)
        payload = IntegrationParserService.parse_payload(data)
        external_order_id = payload.get("external_order_id") or payload.get("order_id")
        if not external_order_id:
            raise IntegrationError("external_order_id is required", 400)

        message = IntegrationGatewayService._create_message(connection_id, "LIS_RESULT", payload, actor_email)
        result_msg = LISResultMessage(
            message_id=message.id,
            external_order_id=external_order_id,
            result_code=payload.get("result_code"),
            result_value=payload.get("result_value"),
            status=LIS_RESULT_RELEASED,
            released_at=datetime.utcnow(),
        )
        db.session.add(result_msg)
        message.status = INTEGRATION_MESSAGE_PROCESSED
        message.processed_at = datetime.utcnow()
        IntegrationGatewayService._write_audit(
            "LIS_RESULT_PROCESSED",
            connection_id=connection_id,
            message_id=message.id,
            detail=external_order_id,
            actor_email=actor_email,
        )
        db.session.commit()
        return {"message": message.to_dict(), "result": result_msg.to_dict()}


class HISPatientService:

    @staticmethod
    def process_patient(connection_id, data, actor_email="SYSTEM"):
        IntegrationGatewayService._get_connection_or_raise(connection_id)
        payload = IntegrationParserService.parse_payload(data)
        external_patient_id = payload.get("external_patient_id") or payload.get("patient_id")
        if not external_patient_id:
            raise IntegrationError("external_patient_id is required", 400)

        message = IntegrationGatewayService._create_message(connection_id, "HIS_PATIENT", payload, actor_email)
        patient_msg = HISPatientMessage(
            message_id=message.id,
            external_patient_id=external_patient_id,
            full_name=payload.get("full_name"),
            phone=payload.get("phone"),
            date_of_birth=payload.get("date_of_birth"),
            status=HIS_PATIENT_SYNCED,
        )
        db.session.add(patient_msg)

        if payload.get("phone") and not Patient.query.filter_by(phone=payload.get("phone")).first():
            db.session.add(
                Patient(
                    patient_code=f"HIS-{external_patient_id}",
                    full_name=payload.get("full_name") or "HIS Patient",
                    phone=payload.get("phone"),
                )
            )

        message.status = INTEGRATION_MESSAGE_PROCESSED
        message.processed_at = datetime.utcnow()
        IntegrationGatewayService._write_audit(
            "HIS_PATIENT_PROCESSED",
            connection_id=connection_id,
            message_id=message.id,
            detail=external_patient_id,
            actor_email=actor_email,
        )
        db.session.commit()
        return {"message": message.to_dict(), "patient_message": patient_msg.to_dict()}
