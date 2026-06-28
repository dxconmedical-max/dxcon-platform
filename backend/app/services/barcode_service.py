import uuid


def medical_order_barcode(order_code):
    return f"DXO-{order_code}"


def medical_order_qr_payload(order_code):
    return f"DXCON:MEDICAL_ORDER:{order_code}"


def medical_sample_barcode(sample_code):
    return f"DXS-{sample_code}"


def medical_sample_qr_payload(sample_code):
    return f"DXCON:MEDICAL_SAMPLE:{sample_code}"


def generate_order_codes(order_code):
    return {
        "barcode_value": medical_order_barcode(order_code),
        "qr_payload": medical_order_qr_payload(order_code),
    }


def generate_sample_codes(sample_code):
    return {
        "barcode_value": medical_sample_barcode(sample_code),
        "qr_payload": medical_sample_qr_payload(sample_code),
    }


def generate_unique_sample_code(prefix="SMP"):
    token = str(uuid.uuid4())[:8].upper()
    return f"{prefix}-{token}"
