#!/usr/bin/env python3
"""Seed demo healthcare standards data."""

import os
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app import create_app
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
from app.standards.fhir.fhir_resource import sample_diagnostic_report
from app.standards.hl7.hl7_builder import build_oru_message
from app.standards.registry import SUPPORTED_CODE_SYSTEMS
from app.services.healthcare_standards_service import DICOMMetadataService


def seed_code_systems():
    created = 0
    for system_code, meta in SUPPORTED_CODE_SYSTEMS.items():
        if StandardCodeSystem.query.filter_by(system_code=system_code).first():
            continue
        db.session.add(
            StandardCodeSystem(
                system_code=system_code,
                name=meta["name"],
                version=meta["version"],
                status="ACTIVE",
            )
        )
        created += 1
    db.session.commit()
    return created


def seed_codes(system_code, prefix, display_prefix, count=100):
    system = StandardCodeSystem.query.filter_by(system_code=system_code).first()
    if system is None:
        return 0
    added = 0
    for index in range(1, count + 1):
        code = f"{prefix}{index:04d}"
        if StandardCode.query.filter_by(system_id=system.id, code=code).first():
            continue
        db.session.add(
            StandardCode(
                system_id=system.id,
                code=code,
                display=f"{display_prefix} {index}",
                category="DEMO",
            )
        )
        added += 1
    batch = StandardImportBatch(
        batch_code=f"BATCH-{system_code}-{uuid.uuid4().hex[:8].upper()}",
        system_code=system_code,
        record_count=added,
        status="COMPLETED",
    )
    db.session.add(batch)
    db.session.commit()
    return added


def seed_service_mappings(count=50):
    loinc_system = StandardCodeSystem.query.filter_by(system_code="LOINC").first()
    if loinc_system is None:
        return 0
    loinc_codes = StandardCode.query.filter_by(system_id=loinc_system.id).limit(count).all()
    added = 0
    for index, code_row in enumerate(loinc_codes, start=1):
        source_code = f"SVC-{index:03d}"
        if StandardMapping.query.filter_by(source_type="DXCON_SERVICE", source_code=source_code).first():
            continue
        db.session.add(
            StandardMapping(
                mapping_code=f"MAP-SVC-{index:03d}",
                source_type="DXCON_SERVICE",
                source_code=source_code,
                target_system="LOINC",
                target_code=code_row.code,
                target_display=code_row.display,
            )
        )
        added += 1
    db.session.commit()
    return added


def seed_samples():
    oru = build_oru_message("PAT-001", "ORD-001", "58410-2", "95")
    fhir_report = sample_diagnostic_report()
    dicom = DICOMMetadataService.save_metadata(
        {
            "study": {
                "study_uid": "1.2.840.113619.2.55.3.604688506.867.1234567890",
                "patient_id": "PAT-001",
                "accession_number": "ACC-001",
                "study_date": "20260701",
                "modality": "CT",
                "description": "Demo CT Head",
            },
            "series": [
                {
                    "series_uid": "1.2.840.113619.2.55.3.604688506.867.9876543210",
                    "series_number": "1",
                    "modality": "CT",
                    "body_part": "HEAD",
                    "instances": [
                        {
                            "sop_instance_uid": "1.2.840.113619.2.55.3.604688506.867.1111111111",
                            "instance_number": "1",
                            "transfer_syntax": "1.2.840.10008.1.2.1",
                        }
                    ],
                }
            ],
        }
    )
    return {"hl7_oru": oru, "fhir_report": fhir_report, "dicom": dicom}


def seed_all():
    systems = seed_code_systems()
    loinc = seed_codes("LOINC", "LNC-", "LOINC Demo")
    icd10 = seed_codes("ICD10", "I10-", "ICD-10 Demo")
    snomed = seed_codes("SNOMED_CT", "SCT-", "SNOMED Demo")
    mappings = seed_service_mappings(50)
    samples = seed_samples()
    return {
        "systems": systems,
        "loinc": loinc,
        "icd10": icd10,
        "snomed": snomed,
        "mappings": mappings,
        "samples": samples,
    }


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        result = seed_all()
        print("OK: code systems", result["systems"])
        print("OK: LOINC codes", result["loinc"])
        print("OK: ICD10 codes", result["icd10"])
        print("OK: SNOMED codes", result["snomed"])
        print("OK: service mappings", result["mappings"])
        print("OK: sample HL7 ORU generated")
        print("OK: sample FHIR DiagnosticReport generated")
        print("OK: sample DICOM metadata saved", result["samples"]["dicom"]["study"]["study_uid"])
    print("\nSTANDARDS DEMO SEED PASSED\n")


if __name__ == "__main__":
    main()
