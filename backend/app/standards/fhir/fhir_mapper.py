from app.standards.fhir.fhir_resource import sample_diagnostic_report, sample_patient, sample_service_request
from app.standards.mapping import StandardsMappingService
from app.standards.normalizer import normalize_order, normalize_patient, normalize_result


def map_order_to_fhir(order_payload):
    normalized = normalize_order(order_payload)
    mapping = StandardsMappingService.map_dxcon_service(normalized.get("service_code") or "CBC")
    target = mapping["mappings"][0] if mapping["mappings"] else {}
    resource = sample_service_request(
        order_id=normalized.get("order_id") or "ORD-001",
        patient_id=normalized.get("patient_id") or "PAT-001",
    )
    if target:
        resource["code"] = {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": target.get("target_code"),
                    "display": target.get("target_display"),
                }
            ]
        }
    return {"normalized": normalized, "mapping": mapping, "resource": resource}


def map_result_to_fhir(result_payload):
    normalized = normalize_result(result_payload)
    mapping = StandardsMappingService.map_dxcon_service(result_payload.get("service_code") or "CBC")
    target = mapping["mappings"][0] if mapping["mappings"] else {}
    resource = sample_diagnostic_report(
        patient_id=normalized.get("patient_id") or "PAT-001",
        order_id=normalized.get("order_id") or "ORD-001",
    )
    observation = {
        "resourceType": "Observation",
        "id": "OBS-001",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": target.get("target_code", "58410-2")}]},
        "valueQuantity": {"value": normalized.get("value"), "unit": normalized.get("unit")},
        "referenceRange": [{"text": normalized.get("reference_range")}],
    }
    return {
        "normalized": normalized,
        "mapping": mapping,
        "diagnostic_report": resource,
        "observation": observation,
    }


def map_patient_to_fhir(patient_payload):
    normalized = normalize_patient(patient_payload or {})
    patient_id = normalized.get("patient_id") or "PAT-001"
    resource = sample_patient(patient_id=patient_id)
    if normalized.get("name"):
        parts = str(normalized["name"]).split("^")
        resource["name"] = [
            {
                "family": parts[0] if parts else "Patient",
                "given": [parts[1]] if len(parts) > 1 else ["Demo"],
            }
        ]
    if normalized.get("gender"):
        resource["gender"] = str(normalized["gender"]).lower()
    if normalized.get("birth_date"):
        resource["birthDate"] = str(normalized["birth_date"]).replace("/", "-")[:10]
    return {"normalized": normalized, "resource": resource}


def map_observation_to_fhir(result_payload):
    mapped = map_result_to_fhir(result_payload or {})
    return {
        "normalized": mapped["normalized"],
        "mapping": mapped["mapping"],
        "observation": mapped["observation"],
    }
