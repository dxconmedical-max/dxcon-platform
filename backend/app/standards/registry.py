SUPPORTED_CODE_SYSTEMS = {
    "LOINC": {"name": "LOINC", "version": "2.77"},
    "ICD10": {"name": "ICD-10", "version": "2026"},
    "SNOMED_CT": {"name": "SNOMED CT", "version": "2026-03"},
    "FHIR_R4": {"name": "FHIR R4", "version": "4.0.1"},
    "HL7_V2": {"name": "HL7 v2.x", "version": "2.5.1"},
    "DICOM": {"name": "DICOM", "version": "2024b"},
}

FHIR_RESOURCE_TYPES = (
    "Patient",
    "Practitioner",
    "Organization",
    "ServiceRequest",
    "Specimen",
    "Observation",
    "DiagnosticReport",
)

HL7_MESSAGE_TYPES = ("ADT", "ORM", "ORU")


class StandardsRegistry:
    @classmethod
    def list_code_systems(cls):
        return [
            {"system_code": code, **meta, "status": "ACTIVE"}
            for code, meta in SUPPORTED_CODE_SYSTEMS.items()
        ]

    @classmethod
    def is_supported_system(cls, system_code: str) -> bool:
        return system_code in SUPPORTED_CODE_SYSTEMS

    @classmethod
    def fhir_resource_types(cls):
        return list(FHIR_RESOURCE_TYPES)

    @classmethod
    def hl7_message_types(cls):
        return list(HL7_MESSAGE_TYPES)
