import json
import uuid

from app.extensions.db import db
from app.models.healthcare_standards import (
    DICOMInstanceMetadata,
    DICOMSeriesMetadata,
    DICOMStudyMetadata,
    StandardCode,
    StandardCodeSystem,
    StandardImportBatch,
    StandardMapping,
)
from app.standards.fhir.fhir_mapper import map_order_to_fhir, map_result_to_fhir
from app.standards.fhir.fhir_validator import validate_fhir_resource
from app.standards.hl7.hl7_builder import build_oru_message
from app.standards.hl7.hl7_parser import parse_hl7
from app.standards.hl7.hl7_validator import validate_hl7
from app.standards.mapping import StandardsMappingService
from app.standards.registry import StandardsRegistry
from app.standards.validators import log_validation, validate_code_reference


class StandardsError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class HealthcareStandardsService:
    @staticmethod
    def list_code_systems():
        try:
            db_rows = StandardCodeSystem.query.order_by(StandardCodeSystem.system_code).all()
            if db_rows:
                return {"count": len(db_rows), "code_systems": [row.to_dict() for row in db_rows]}
        except Exception:
            db.session.rollback()
        return {"count": len(StandardsRegistry.list_code_systems()), "code_systems": StandardsRegistry.list_code_systems()}

    @staticmethod
    def list_codes(system_code=None, limit=100):
        query = StandardCode.query.join(StandardCodeSystem)
        if system_code:
            query = query.filter(StandardCodeSystem.system_code == system_code)
        rows = query.order_by(StandardCode.code).limit(min(limit, 500)).all()
        return {"count": len(rows), "codes": [row.to_dict() for row in rows]}


class HL7StandardsService:
    @staticmethod
    def parse(raw_message):
        try:
            message = parse_hl7(raw_message)
            log_validation("HL7_V2", message.message_type, "PARSED", message.to_dict())
            return message.to_dict()
        except ValueError as exc:
            raise StandardsError(str(exc))

    @staticmethod
    def validate(raw_message):
        result = validate_hl7(raw_message)
        log_validation("HL7_V2", result.get("message_type"), "VALID" if result["valid"] else "INVALID", result)
        return result

    @staticmethod
    def build_oru(data):
        data = data or {}
        message = build_oru_message(
            patient_id=data.get("patient_id") or "PAT-001",
            order_id=data.get("order_id") or "ORD-001",
            observation_code=data.get("observation_code") or "58410-2",
            value=data.get("value") or "95",
            unit=data.get("unit") or "mg/dL",
        )
        parsed = parse_hl7(message)
        return {"message": message, "parsed": parsed.to_dict()}


class FHIRStandardsService:
    @staticmethod
    def validate(resource):
        result = validate_fhir_resource(resource or {})
        log_validation("FHIR_R4", result.get("resource_type"), "VALID" if result["valid"] else "INVALID", result)
        return result

    @staticmethod
    def map_result(payload):
        return map_result_to_fhir(payload or {})

    @staticmethod
    def map_order(payload):
        return map_order_to_fhir(payload or {})


class DICOMMetadataService:
    @staticmethod
    def save_metadata(data):
        study_data = data.get("study") or data
        study_uid = study_data.get("study_uid") or f"1.2.840.{uuid.uuid4().hex[:16]}"
        study = DICOMStudyMetadata.query.filter_by(study_uid=study_uid).first()
        if study is None:
            study = DICOMStudyMetadata(study_uid=study_uid)
            db.session.add(study)
        study.patient_id = study_data.get("patient_id")
        study.accession_number = study_data.get("accession_number")
        study.study_date = study_data.get("study_date")
        study.modality = study_data.get("modality")
        study.description = study_data.get("description")
        study.metadata_json = json.dumps(study_data.get("metadata") or {})
        db.session.flush()

        series_list = []
        for series_data in data.get("series") or []:
            series_uid = series_data.get("series_uid") or f"1.2.840.{uuid.uuid4().hex[:16]}"
            series = DICOMSeriesMetadata.query.filter_by(series_uid=series_uid).first()
            if series is None:
                series = DICOMSeriesMetadata(study_id=study.id, series_uid=series_uid)
                db.session.add(series)
            series.series_number = series_data.get("series_number")
            series.modality = series_data.get("modality") or study.modality
            series.body_part = series_data.get("body_part")
            series.metadata_json = json.dumps(series_data.get("metadata") or {})
            db.session.flush()

            instances = []
            for instance_data in series_data.get("instances") or []:
                sop_uid = instance_data.get("sop_instance_uid") or f"1.2.840.{uuid.uuid4().hex[:16]}"
                instance = DICOMInstanceMetadata.query.filter_by(sop_instance_uid=sop_uid).first()
                if instance is None:
                    instance = DICOMInstanceMetadata(series_id=series.id, sop_instance_uid=sop_uid)
                    db.session.add(instance)
                instance.instance_number = instance_data.get("instance_number")
                instance.transfer_syntax = instance_data.get("transfer_syntax")
                instance.metadata_json = json.dumps(instance_data.get("metadata") or {})
                instances.append(instance.to_dict())
            series_list.append({**series.to_dict(), "instances": instances})

        db.session.commit()
        return {"study": study.to_dict(), "series": series_list}

    @staticmethod
    def list_studies():
        rows = DICOMStudyMetadata.query.order_by(DICOMStudyMetadata.created_at.desc()).all()
        return {"count": len(rows), "studies": [row.to_dict() for row in rows]}

    @staticmethod
    def get_study(study_id):
        row = DICOMStudyMetadata.query.filter_by(id=study_id).first()
        if row is None:
            raise StandardsError("Study not found", 404)
        series = DICOMSeriesMetadata.query.filter_by(study_id=row.id).all()
        payload = row.to_dict()
        payload["series"] = []
        for item in series:
            instances = DICOMInstanceMetadata.query.filter_by(series_id=item.id).all()
            payload["series"].append({**item.to_dict(), "instances": [inst.to_dict() for inst in instances]})
        return payload


class CodeMappingService:
    @staticmethod
    def create_mapping(data):
        try:
            return StandardsMappingService.create_mapping(data)
        except ValueError as exc:
            raise StandardsError(str(exc))

    @staticmethod
    def list_mappings(source_type=None, target_system=None):
        return StandardsMappingService.list_mappings(source_type, target_system)

    @staticmethod
    def resolve(data):
        source_type = data.get("source_type")
        source_code = data.get("source_code")
        if not source_type or not source_code:
            raise StandardsError("source_type and source_code are required")
        return StandardsMappingService.resolve(source_type, source_code, data.get("target_system"))

    @staticmethod
    def validate_reference(system_code, code):
        return validate_code_reference(system_code, code)
