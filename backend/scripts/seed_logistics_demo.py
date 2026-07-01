import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import create_app
from app.extensions.db import db
from app.services.logistics_platform_service import (
    DispatchBoardService,
    DriverService,
    ProofOfDeliveryService,
    RouteOptimizationService,
    VehicleService,
)


def seed_logistics_demo(force=False):
    from app.models.logistics_driver import DriverProfile, Vehicle
    from app.models.logistics_route import DispatchAssignment, RoutePlan

    if not force and DriverProfile.query.count() >= 5:
        return {
            "drivers": DriverProfile.query.count(),
            "vehicles": Vehicle.query.count(),
            "routes": RoutePlan.query.count(),
            "assignments": DispatchAssignment.query.count(),
            "skipped": True,
        }

    drivers = []
    for idx in range(8):
        driver = DriverService.create_driver(
            {
                "profile_code": f"DRV-{idx + 1:03d}",
                "full_name": f"Driver {idx + 1}",
                "phone": f"09{random.randint(10000000, 99999999)}",
                "hub_city": random.choice(["HCMC", "Hanoi", "Da Nang"]),
            }
        )
        drivers.append(driver)

    vehicles = []
    for idx in range(6):
        vehicle = VehicleService.create_vehicle(
            {
                "vehicle_code": f"VEH-{idx + 1:03d}",
                "plate_number": f"59A-{10000 + idx}",
                "vehicle_type": random.choice(["VAN", "MOTORBIKE", "TRUCK"]),
                "latitude": 10.0452 + idx * 0.01,
                "longitude": 105.7469 + idx * 0.01,
            }
        )
        vehicles.append(vehicle)

    routes = []
    for idx in range(5):
        route = RouteOptimizationService.create_route(
            {
                "route_code": f"RTE-{idx + 1:03d}",
                "driver_profile_id": drivers[idx % len(drivers)].id,
                "vehicle_id": vehicles[idx % len(vehicles)].id,
                "start_latitude": 10.0452,
                "start_longitude": 105.7469,
                "stops": [
                    {
                        "address": f"Stop A-{idx}",
                        "latitude": 10.05 + idx * 0.01,
                        "longitude": 105.75 + idx * 0.01,
                    },
                    {
                        "address": f"Stop B-{idx}",
                        "latitude": 10.06 + idx * 0.01,
                        "longitude": 105.76 + idx * 0.01,
                    },
                    {
                        "address": f"Stop C-{idx}",
                        "latitude": 10.07 + idx * 0.01,
                        "longitude": 105.77 + idx * 0.01,
                    },
                ],
            }
        )
        RouteOptimizationService.optimize_route(route.id)
        routes.append(route)

    for idx in range(4):
        DispatchBoardService.assign(
            {
                "driver_profile_id": drivers[idx].id,
                "vehicle_id": vehicles[idx].id,
                "route_plan_id": routes[idx].id,
                "priority": random.choice(["NORMAL", "URGENT"]),
                "actor": "seed",
            }
        )

    for idx in range(10):
        ProofOfDeliveryService.record_gps(
            {
                "driver_profile_id": drivers[idx % len(drivers)].id,
                "vehicle_id": vehicles[idx % len(vehicles)].id,
                "latitude": 10.0452 + random.uniform(-0.05, 0.05),
                "longitude": 105.7469 + random.uniform(-0.05, 0.05),
                "speed": random.uniform(10, 45),
            }
        )

    return {
        "drivers": DriverProfile.query.count(),
        "vehicles": Vehicle.query.count(),
        "routes": RoutePlan.query.count(),
        "assignments": DispatchAssignment.query.count(),
        "skipped": False,
    }


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        print(seed_logistics_demo(force="--force" in sys.argv))
