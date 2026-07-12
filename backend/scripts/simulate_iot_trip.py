#!/usr/bin/env python3
"""Simulate IoT trip telemetry for development and automated tests only."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["IOT_SIMULATOR_ENABLED"] = "true"


def main() -> int:
    parser = argparse.ArgumentParser(description="IoT trip telemetry simulator (SIMULATED)")
    parser.add_argument("--organization-id", default="sim-org")
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--excursion", action="store_true", help="Trigger temperature excursion")
    parser.add_argument("--offline", action="store_true", help="Simulate device offline gap")
    args = parser.parse_args()

    from app import create_app
    from app.extensions.db import db
    from app.iot_platform.auth import simulator_allowed
    from app.iot_platform.service import create_trip, process_telemetry_batch, register_device

    if not simulator_allowed():
        print("ERROR: Simulator disabled in this environment. Set IOT_SIMULATOR_ENABLED=true for non-production.")
        return 1

    app = create_app()
    with app.app_context():
        db.create_all()
        device = register_device(
            {"device_type": "cold_chain_tracker", "device_code": f"SIM-{int(time.time())}"},
            organization_id=args.organization_id,
            actor="simulator",
        )
        db.session.commit()
        trip = create_trip({}, organization_id=args.organization_id)
        db.session.commit()
        device_id = device["device"]["id"]
        base_lat, base_lng = 10.7769, 106.7009
        readings = []
        for i in range(args.steps):
            temp = 4.5 + (i * 0.2)
            if args.excursion and i >= args.steps - 2:
                temp = 14.0
            readings.append({
                "device_id": device_id,
                "recorded_at": datetime.utcnow().isoformat(),
                "temperature_c": temp,
                "humidity_percent": 55.0,
                "latitude": base_lat + i * 0.001,
                "longitude": base_lng + i * 0.001,
                "speed_kph": 30.0,
                "battery_percent": max(10, 100 - i * 5),
                "sequence_number": i + 1,
                "trip_id": trip["id"],
                "metadata": {"label": "SIMULATED", "simulator": True},
            })
            if args.offline and i == args.steps // 2:
                time.sleep(0.1)
        result = process_telemetry_batch(readings, organization_id=args.organization_id, simulated=True)
        db.session.commit()
        print(json.dumps({"status": "SIMULATED", "device_id": device_id, "trip_id": trip["id"], **result}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
