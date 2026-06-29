import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import create_app
from app.extensions.db import db
from app.models.logistics_tracking import ChainOfCustodyEvent, GPSPing
from app.services.logistics_platform_service import (
    DispatchBoardService,
    ProofOfDeliveryService,
    RouteOptimizationService,
)
from scripts.seed_logistics_demo import seed_logistics_demo


def verify_models_import():
    from app.models.logistics_driver import DriverProfile, Vehicle
    from app.models.logistics_route import DispatchAssignment, ETAEstimate, RoutePlan, RouteStop
    from app.models.logistics_tracking import DeliveryProof

    models = [
        DriverProfile,
        Vehicle,
        RoutePlan,
        RouteStop,
        DispatchAssignment,
        ETAEstimate,
        GPSPing,
        DeliveryProof,
        ChainOfCustodyEvent,
    ]
    for model in models:
        assert model.__tablename__
    print("OK: logistics models import")


def verify_routes(app):
    routes = {str(rule) for rule in app.url_map.iter_rules()}
    required_api = [
        "/api/v1/logistics/drivers",
        "/api/v1/logistics/vehicles",
        "/api/v1/logistics/routes",
        "/api/v1/logistics/routes/optimize",
        "/api/v1/logistics/dispatch-board",
        "/api/v1/logistics/assign",
        "/api/v1/logistics/gps",
        "/api/v1/logistics/proof",
    ]
    required_web = [
        "/logistics",
        "/logistics/dispatch",
        "/logistics/routes",
        "/logistics/live-map",
    ]
    ok = True
    for route in required_api + required_web:
        if route in routes:
            print("OK:", route)
        else:
            print("MISSING:", route)
            ok = False
    return ok


def verify_seed_and_flow():
    summary = seed_logistics_demo(force=True)
    if summary.get("drivers", 0) < 5:
        print("MISSING: demo drivers")
        return False
    print(f"OK: drivers={summary['drivers']}, vehicles={summary['vehicles']}")
    print(f"OK: routes={summary['routes']}, assignments={summary['assignments']}")

    route = RouteOptimizationService.list_routes()["items"][0]
    optimized = RouteOptimizationService.optimize_route(route["id"])
    if optimized["status"] != "OPTIMIZED":
        print("MISSING: route optimization")
        return False
    print("OK: route optimization")

    board = DispatchBoardService.get_board()
    if "summary" not in board:
        print("MISSING: dispatch board")
        return False
    print("OK: dispatch board")

    ProofOfDeliveryService.record_gps(
        {"latitude": 10.0452, "longitude": 105.7469, "speed": 20}
    )
    if GPSPing.query.count() < 1:
        print("MISSING: gps ping")
        return False
    print("OK: gps ping flow")
    return True


def verify_api(client):
    response = client.get("/api/v1/logistics/drivers")
    if response.status_code != 200:
        print("MISSING: drivers API")
        return False
    print("OK: drivers API")

    response = client.get("/api/v1/logistics/dispatch-board")
    if response.status_code != 200:
        print("MISSING: dispatch board API")
        return False
    print("OK: dispatch board API")

    for path in ("/logistics/routes", "/logistics/live-map"):
        response = client.get(path)
        if response.status_code != 200:
            print("MISSING:", path)
            return False
        print("OK:", path)
    return True


app = create_app()

with app.app_context():
    db.create_all()
    print("\n=== DXCON LOGISTICS V2 VERIFY ===\n")
    verify_models_import()
    routes_ok = verify_routes(app)
    flow_ok = verify_seed_and_flow()
    api_ok = verify_api(app.test_client())

    score = sum([routes_ok, flow_ok, api_ok])
    print(f"\nVerification score: {score}/3")
    if score == 3:
        print("LOGISTICS V2 VERIFY PASSED\n")
    else:
        print("LOGISTICS V2 VERIFY FAILED\n")
        sys.exit(1)
