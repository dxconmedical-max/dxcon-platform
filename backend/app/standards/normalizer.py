def normalize_patient(payload):
    return {
        "patient_id": payload.get("patient_id") or payload.get("id"),
        "name": payload.get("name") or payload.get("patient_name"),
        "gender": payload.get("gender"),
        "birth_date": payload.get("birth_date") or payload.get("dob"),
    }


def normalize_order(payload):
    return {
        "order_id": payload.get("order_id") or payload.get("placer_order_number"),
        "service_code": payload.get("service_code") or payload.get("test_code"),
        "patient_id": payload.get("patient_id"),
        "priority": payload.get("priority") or "ROUTINE",
    }


def normalize_result(payload):
    return {
        "result_id": payload.get("result_id") or payload.get("observation_id"),
        "order_id": payload.get("order_id"),
        "patient_id": payload.get("patient_id"),
        "value": payload.get("value"),
        "unit": payload.get("unit"),
        "reference_range": payload.get("reference_range"),
        "status": payload.get("status") or "FINAL",
    }


def normalize_hl7_payload(message_type, segments):
    if message_type == "ADT":
        pid = segments.get("PID", {})
        return {"patient": normalize_patient(pid)}
    if message_type == "ORM":
        orc = segments.get("ORC", {})
        obr = segments.get("OBR", {})
        return {"order": normalize_order({**orc, **obr})}
    if message_type == "ORU":
        pid = segments.get("PID", {})
        obr = segments.get("OBR", {})
        obx = segments.get("OBX", {})
        return {
            "patient": normalize_patient(pid),
            "result": normalize_result({**obr, **obx}),
        }
    return {"segments": segments}
