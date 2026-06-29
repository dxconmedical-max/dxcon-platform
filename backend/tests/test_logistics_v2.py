import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.core.statuses import LOGISTICS_ROUTE_OPTIMIZED
from app.extensions.db import db
from app.models.logistics_route import ETAEstimate, RouteStop
from app.models.logistics_tracking import ChainOfCustodyEvent, DeliveryProof, GPSPing
from app.services.logistics_platform_service import (
    DispatchBoardService,
    DriverService,
    ProofOfDeliveryService,
    RouteOptimizationService,
    VehicleService,
)


class LogisticsV2TestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()

        self.driver = DriverService.create_driver(
            {"full_name": "Logistics Driver", "hub_city": "HCMC"}
        )
        self.vehicle = VehicleService.create_vehicle(
            {"plate_number": "59A-12345", "vehicle_type": "VAN"}
        )
        self.route = RouteOptimizationService.create_route(
            {
                "driver_profile_id": self.driver.id,
                "vehicle_id": self.vehicle.id,
                "start_latitude": 10.0452,
                "start_longitude": 105.7469,
                "stops": [
                    {"address": "Stop 1", "latitude": 10.05, "longitude": 105.75},
                    {"address": "Stop 2", "latitude": 10.06, "longitude": 105.76},
                    {"address": "Stop 3", "latitude": 10.07, "longitude": 105.77},
                ],
            }
        )

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def test_route_optimization_and_eta(self):
        optimized = RouteOptimizationService.optimize_route(self.route.id)
        self.assertEqual(optimized["status"], LOGISTICS_ROUTE_OPTIMIZED)
        self.assertGreater(optimized["total_distance_km"], 0)
        self.assertGreaterEqual(ETAEstimate.query.filter_by(route_plan_id=self.route.id).count(), 3)
        stops = RouteStop.query.filter_by(route_plan_id=self.route.id).order_by(
            RouteStop.stop_sequence.asc()
        ).all()
        self.assertEqual(stops[0].stop_sequence, 1)

    def test_dispatch_assign_gps_and_proof(self):
        RouteOptimizationService.optimize_route(self.route.id)
        assignment = DispatchBoardService.assign(
            {
                "driver_profile_id": self.driver.id,
                "vehicle_id": self.vehicle.id,
                "route_plan_id": self.route.id,
                "actor": "dispatcher",
            }
        )
        self.assertEqual(assignment.status, "ASSIGNED")
        self.assertGreaterEqual(
            ChainOfCustodyEvent.query.filter_by(reference_id=assignment.id).count(), 1
        )

        ping = ProofOfDeliveryService.record_gps(
            {
                "driver_profile_id": self.driver.id,
                "vehicle_id": self.vehicle.id,
                "latitude": 10.0455,
                "longitude": 105.7472,
                "speed": 25,
            }
        )
        self.assertIsNotNone(ping.id)
        self.assertEqual(GPSPing.query.count(), 1)

        stop = RouteStop.query.filter_by(route_plan_id=self.route.id).first()
        proof = ProofOfDeliveryService.record_proof(
            {
                "assignment_id": assignment.id,
                "route_stop_id": stop.id,
                "proof_type": "SIGNATURE",
                "recipient_name": "Patient A",
                "captured_by": "driver",
            }
        )
        self.assertEqual(DeliveryProof.query.count(), 1)
        self.assertEqual(proof.recipient_name, "Patient A")

    def test_dispatch_board(self):
        board = DispatchBoardService.get_board()
        self.assertIn("summary", board)
        self.assertIn("assignments", board)
        self.assertIn("routes", board)

    def test_logistics_api(self):
        response = self.client.get("/api/v1/logistics/drivers")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.get_json()["pagination"]["total"], 1)

        response = self.client.get("/api/v1/logistics/vehicles")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(
            "/api/v1/logistics/routes/optimize",
            json={"route_id": self.route.id},
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/api/v1/logistics/dispatch-board")
        self.assertEqual(response.status_code, 200)

        assign_response = self.client.post(
            "/api/v1/logistics/assign",
            json={
                "driver_profile_id": self.driver.id,
                "vehicle_id": self.vehicle.id,
                "route_plan_id": self.route.id,
            },
        )
        self.assertEqual(assign_response.status_code, 201)
        assignment_id = assign_response.get_json()["assignment"]["id"]

        response = self.client.post(
            "/api/v1/logistics/gps",
            json={
                "driver_profile_id": self.driver.id,
                "latitude": 10.0452,
                "longitude": 105.7469,
            },
        )
        self.assertEqual(response.status_code, 201)

        response = self.client.post(
            "/api/v1/logistics/proof",
            json={
                "assignment_id": assignment_id,
                "proof_type": "PHOTO",
                "proof_url": "/uploads/proof.jpg",
                "recipient_name": "Patient B",
            },
        )
        self.assertEqual(response.status_code, 201)


if __name__ == "__main__":
    unittest.main()
