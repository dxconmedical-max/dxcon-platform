SUPPORTED_RESOURCES = {
    "Patient": ["id", "name"],
    "Practitioner": ["id", "name"],
    "Organization": ["id", "name"],
    "ServiceRequest": ["id", "status", "subject"],
    "Specimen": ["id", "status"],
    "Observation": ["id", "status", "code", "valueQuantity"],
    "DiagnosticReport": ["id", "status", "code", "subject"],
}


def validate_fhir_resource(resource):
    resource_type = resource.get("resourceType")
    if resource_type not in SUPPORTED_RESOURCES:
        return {
            "valid": False,
            "errors": [f"Unsupported resourceType: {resource_type}"],
            "resource_type": resource_type,
        }
    errors = []
    for field in SUPPORTED_RESOURCES[resource_type]:
        if field not in resource:
            errors.append(f"Missing required field: {field}")
    return {
        "valid": not errors,
        "errors": errors,
        "resource_type": resource_type,
    }
