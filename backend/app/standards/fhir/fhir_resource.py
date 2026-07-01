def sample_diagnostic_report(patient_id="PAT-001", order_id="ORD-001"):
    return {
        "resourceType": "DiagnosticReport",
        "id": "DR-001",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2", "display": "CBC panel"}]},
        "subject": {"reference": f"Patient/{patient_id}"},
        "basedOn": [{"reference": f"ServiceRequest/{order_id}"}],
        "result": [{"reference": "Observation/OBS-001"}],
    }


def sample_patient(patient_id="PAT-001"):
    return {
        "resourceType": "Patient",
        "id": patient_id,
        "name": [{"family": "Patient", "given": ["Demo"]}],
        "gender": "male",
        "birthDate": "1980-01-01",
    }


def sample_service_request(order_id="ORD-001", patient_id="PAT-001"):
    return {
        "resourceType": "ServiceRequest",
        "id": order_id,
        "status": "active",
        "intent": "order",
        "subject": {"reference": f"Patient/{patient_id}"},
        "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2"}]},
    }
