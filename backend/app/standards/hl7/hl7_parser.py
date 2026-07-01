from app.standards.hl7.hl7_message import HL7Message


def _parse_segment_fields(segment_name, fields):
    if segment_name == "MSH":
        return {
            "encoding": fields[0] if fields else "|",
            "sending_application": fields[1] if len(fields) > 1 else "",
            "sending_facility": fields[2] if len(fields) > 2 else "",
            "message_type": fields[7] if len(fields) > 7 else "",
            "message_control_id": fields[8] if len(fields) > 8 else "",
        }
    if segment_name == "PID":
        return {
            "patient_id": fields[2] if len(fields) > 2 else fields[0] if fields else "",
            "patient_name": fields[4] if len(fields) > 4 else "",
            "birth_date": fields[6] if len(fields) > 6 else "",
            "gender": fields[7] if len(fields) > 7 else "",
        }
    if segment_name == "ORC":
        return {
            "order_control": fields[0] if fields else "",
            "placer_order_number": fields[1] if len(fields) > 1 else "",
        }
    if segment_name == "OBR":
        return {
            "placer_order_number": fields[1] if len(fields) > 1 else "",
            "test_code": fields[3] if len(fields) > 3 else "",
            "observation_datetime": fields[6] if len(fields) > 6 else "",
        }
    if segment_name == "OBX":
        return {
            "value_type": fields[1] if len(fields) > 1 else "",
            "observation_id": fields[2] if len(fields) > 2 else "",
            "value": fields[4] if len(fields) > 4 else "",
            "unit": fields[5] if len(fields) > 5 else "",
            "reference_range": fields[6] if len(fields) > 6 else "",
            "status": fields[10] if len(fields) > 10 else "",
        }
    return {"fields": fields}


def parse_hl7(raw_message: str) -> HL7Message:
    text = (raw_message or "").strip().replace("\r\n", "\r").replace("\n", "\r")
    lines = [line for line in text.split("\r") if line.strip()]
    if not lines:
        raise ValueError("HL7 message is empty")

    segments = {}
    message_type = "UNKNOWN"
    for line in lines:
        parts = line.split("|")
        name = parts[0]
        fields = parts[1:]
        segments[name] = _parse_segment_fields(name, fields)
        if name == "MSH":
            msg_type = segments[name].get("message_type", "")
            message_type = msg_type.split("^")[0] if msg_type else "UNKNOWN"

    return HL7Message(message_type=message_type, segments=segments, raw=text)
