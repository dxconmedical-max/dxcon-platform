from app.standards.hl7.hl7_parser import parse_hl7
from app.standards.normalizer import normalize_hl7_payload
from app.standards.registry import StandardsRegistry


REQUIRED_SEGMENTS = {
    "ADT": ["MSH", "PID"],
    "ORM": ["MSH", "PID", "ORC", "OBR"],
    "ORU": ["MSH", "PID", "OBR", "OBX"],
}


def validate_hl7(raw_message: str):
    message = parse_hl7(raw_message)
    errors = []
    if message.message_type not in StandardsRegistry.hl7_message_types():
        errors.append(f"Unsupported message type: {message.message_type}")
    required = REQUIRED_SEGMENTS.get(message.message_type, ["MSH"])
    for segment in required:
        if segment not in message.segments:
            errors.append(f"Missing required segment: {segment}")
    normalized = normalize_hl7_payload(message.message_type, message.segments)
    return {
        "valid": not errors,
        "errors": errors,
        "message_type": message.message_type,
        "normalized": normalized,
    }
