def shipment_qr_payload(shipment_code):
    return f"DXCON:SHIPMENT:{shipment_code}"


def sample_qr_payload(sample_code):
    return f"DXCON:SAMPLE:{sample_code}"


def box_qr_payload(box_code):
    return f"DXCON:BOX:{box_code}"


def parse_qr_payload(payload):
    parts = payload.split(":")

    if len(parts) != 3:
        return {
            "valid": False,
            "type": None,
            "code": None
        }

    namespace, object_type, code = parts

    if namespace != "DXCON":
        return {
            "valid": False,
            "type": None,
            "code": None
        }

    return {
        "valid": True,
        "type": object_type,
        "code": code
    }
