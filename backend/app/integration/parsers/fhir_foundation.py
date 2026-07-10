"""FHIR R4 foundation — Epic 3.5 (subset, not conformance tested)."""

from __future__ import annotations

from typing import Any

SUPPORTED_RESOURCES = (
    "Patient", "ServiceRequest", "Specimen", "Observation",
    "DiagnosticReport", "Organization", "Practitioner",
)


def map_fhir_resource(resource: dict[str, Any]) -> dict[str, Any]:
    rtype = resource.get("resourceType", "")
    if rtype not in SUPPORTED_RESOURCES:
        return {"valid": False, "error": "unsupported resource", "resource_type": rtype}
    canonical: dict[str, Any] = {"resource_type": rtype, "id": resource.get("id")}
    if rtype == "Patient":
        names = resource.get("name") or []
        canonical["full_name"] = names[0].get("text") if names else None
        canonical["patient_code"] = resource.get("id")
    elif rtype == "Observation":
        canonical["test_code"] = (resource.get("code") or {}).get("text")
        canonical["result_value"] = resource.get("valueString") or (resource.get("valueQuantity") or {}).get("value")
    elif rtype == "ServiceRequest":
        canonical["order_code"] = resource.get("id")
    return {"valid": True, "canonical": canonical, "foundation_only": True}
