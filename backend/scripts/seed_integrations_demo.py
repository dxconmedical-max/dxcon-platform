import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import INTEGRATION_TYPE_HIS, INTEGRATION_TYPE_LIS
from app.extensions.db import db
from app.models.integration_connection import IntegrationConnection
from app.services.integration_service import (
    HISPatientService,
    IntegrationGatewayService,
    LISOrderService,
    LISResultService,
)


def seed_integrations_demo():
    if IntegrationConnection.query.first():
        conn = IntegrationConnection.query.first()
        return {"connection_id": conn.id, "already_seeded": True}

    lis_partner = IntegrationGatewayService.ensure_partner(
        {
            "partner_code": "LIS-DEMO-001",
            "partner_name": "Demo LIS",
            "integration_type": INTEGRATION_TYPE_LIS,
            "endpoint_url": "https://lis.demo.local/api",
        }
    )
    his_partner = IntegrationGatewayService.ensure_partner(
        {
            "partner_code": "HIS-DEMO-001",
            "partner_name": "Demo HIS",
            "integration_type": INTEGRATION_TYPE_HIS,
            "endpoint_url": "https://his.demo.local/api",
        }
    )
    lis_conn = IntegrationGatewayService.create_connection(
        {
            "partner_id": lis_partner.id,
            "connection_code": "LIS-CONN-001",
            "protocol": "HL7_FHIR",
        }
    )
    his_conn = IntegrationGatewayService.create_connection(
        {
            "partner_id": his_partner.id,
            "connection_code": "HIS-CONN-001",
            "protocol": "FHIR_R4",
        }
    )

    LISOrderService.process_order(
        lis_conn.id,
        {
            "external_order_id": "LIS-ORD-001",
            "patient_code": "PAT-001",
            "test_codes": ["GLU", "CBC"],
        },
    )
    LISResultService.process_result(
        lis_conn.id,
        {
            "external_order_id": "LIS-ORD-001",
            "result_code": "GLU",
            "result_value": "5.4",
        },
    )
    HISPatientService.process_patient(
        his_conn.id,
        {
            "external_patient_id": "HIS-PAT-001",
            "full_name": "Integration Demo Patient",
            "phone": "0908777888",
            "date_of_birth": "1990-01-01",
        },
    )
    return {"connection_id": lis_conn.id, "his_connection_id": his_conn.id}


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_integrations_demo()
        print("\n=== DXCON INTEGRATIONS DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
