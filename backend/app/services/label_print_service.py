import json
from datetime import datetime

from app.services.barcode_service import (
    generate_order_codes,
    generate_sample_codes,
    medical_order_barcode,
    medical_sample_barcode,
)


class LabelPrintService:

    @staticmethod
    def build_order_label(medical_order, sample=None):
        codes = generate_order_codes(medical_order.order_code)
        payload = {
            "label_type": "MEDICAL_ORDER",
            "label_code": f"LBL-ORD-{medical_order.order_code}",
            "order_code": medical_order.order_code,
            "patient_name": medical_order.patient_name,
            "patient_phone": medical_order.patient_phone,
            "status": medical_order.status,
            "barcode_value": codes["barcode_value"],
            "qr_payload": codes["qr_payload"],
            "generated_at": datetime.utcnow().isoformat(),
        }
        if sample:
            sample_codes = generate_sample_codes(sample.sample_code)
            payload["sample_code"] = sample.sample_code
            payload["sample_barcode"] = sample_codes["barcode_value"]
            payload["sample_qr"] = sample_codes["qr_payload"]
        return payload

    @staticmethod
    def build_sample_label(medical_order, sample):
        order_codes = generate_order_codes(medical_order.order_code)
        sample_codes = generate_sample_codes(sample.sample_code)
        payload = {
            "label_type": "MEDICAL_SAMPLE",
            "label_code": f"LBL-SMP-{sample.sample_code}",
            "order_code": medical_order.order_code,
            "sample_code": sample.sample_code,
            "patient_name": medical_order.patient_name,
            "sample_type": sample.sample_type,
            "order_barcode": order_codes["barcode_value"],
            "sample_barcode": sample_codes["barcode_value"],
            "order_qr": order_codes["qr_payload"],
            "sample_qr": sample_codes["qr_payload"],
            "zpl_preview": (
                f"^XA^FO50,50^A0N,30,30^FD{medical_order.patient_name}^FS"
                f"^FO50,100^BCN,80,Y,N,N^FD{sample_codes['barcode_value']}^FS"
                f"^XZ"
            ),
            "generated_at": datetime.utcnow().isoformat(),
        }
        return payload

    @staticmethod
    def serialize_label(payload):
        return json.dumps(payload, ensure_ascii=False)
