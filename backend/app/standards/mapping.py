from app.extensions.db import db
from app.models.healthcare_standards import StandardCode, StandardCodeSystem, StandardMapping
from app.standards.registry import StandardsRegistry
from app.standards.validators import validate_code_reference


class StandardsMappingService:
    @staticmethod
    def resolve(source_type, source_code, target_system=None):
        query = StandardMapping.query.filter_by(source_type=source_type, source_code=source_code, status="ACTIVE")
        if target_system:
            query = query.filter_by(target_system=target_system)
        rows = query.all()
        return {
            "source_type": source_type,
            "source_code": source_code,
            "count": len(rows),
            "mappings": [row.to_dict() for row in rows],
        }

    @staticmethod
    def create_mapping(data):
        source_type = data.get("source_type")
        source_code = data.get("source_code")
        target_system = data.get("target_system")
        target_code = data.get("target_code")
        if not all([source_type, source_code, target_system, target_code]):
            raise ValueError("source_type, source_code, target_system, and target_code are required")
        if not StandardsRegistry.is_supported_system(target_system):
            raise ValueError(f"Unsupported target system: {target_system}")
        validation = validate_code_reference(target_system, target_code)
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))
        mapping = StandardMapping(
            mapping_code=data.get("mapping_code") or f"MAP-{source_type}-{source_code}-{target_system}",
            source_type=source_type,
            source_code=source_code,
            target_system=target_system,
            target_code=target_code,
            target_display=data.get("target_display") or validation.get("display"),
        )
        db.session.add(mapping)
        db.session.commit()
        return mapping.to_dict()

    @staticmethod
    def list_mappings(source_type=None, target_system=None):
        query = StandardMapping.query
        if source_type:
            query = query.filter_by(source_type=source_type)
        if target_system:
            query = query.filter_by(target_system=target_system)
        rows = query.order_by(StandardMapping.created_at.desc()).all()
        return {"count": len(rows), "mappings": [row.to_dict() for row in rows]}

    @staticmethod
    def map_dxcon_service(service_code):
        return StandardsMappingService.resolve("DXCON_SERVICE", service_code, "LOINC")

    @staticmethod
    def map_dxcon_diagnosis(diagnosis_code):
        return StandardsMappingService.resolve("DXCON_DIAGNOSIS", diagnosis_code, "ICD10")

    @staticmethod
    def map_dxcon_concept(concept_code):
        return StandardsMappingService.resolve("DXCON_CONCEPT", concept_code, "SNOMED_CT")
