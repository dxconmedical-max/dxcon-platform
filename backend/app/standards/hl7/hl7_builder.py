def build_oru_message(patient_id, order_id, observation_code, value, unit="mg/dL"):
    segments = [
        "MSH|^~\\&|DXCON|LAB|HIS|HOSPITAL|20260701120000||ORU^R01|MSG00001|P|2.5.1",
        f"PID|1||{patient_id}||Demo^Patient||19800101|M",
        f"OBR|1|{order_id}|{order_id}|{observation_code}^Complete Blood Count|||20260701113000",
        f"OBX|1|NM|{observation_code}^Result||{value}|{unit}|70-110|N|||F",
    ]
    return "\r".join(segments)


def build_adt_message(patient_id, patient_name="Demo^Patient"):
    segments = [
        "MSH|^~\\&|DXCON|HIS|LAB|HOSPITAL|20260701120000||ADT^A01|MSG00002|P|2.5.1",
        f"PID|1||{patient_id}||{patient_name}||19800101|M",
    ]
    return "\r".join(segments)


def build_orm_message(patient_id, order_id, test_code):
    segments = [
        "MSH|^~\\&|DXCON|HIS|LAB|HOSPITAL|20260701120000||ORM^O01|MSG00003|P|2.5.1",
        f"PID|1||{patient_id}||Demo^Patient||19800101|M",
        f"ORC|NW|{order_id}|{order_id}",
        f"OBR|1|{order_id}|{order_id}|{test_code}^Lab Test",
    ]
    return "\r".join(segments)
