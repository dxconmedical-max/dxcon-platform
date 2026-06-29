from datetime import datetime, timedelta

from app.core.statuses import (
    LOGISTICS_ASSIGNMENT_ASSIGNED,
    LOGISTICS_ASSIGNMENT_PENDING,
    LOGISTICS_CUSTODY_DELIVERY,
    LOGISTICS_CUSTODY_PICKUP,
    LOGISTICS_DRIVER_ACTIVE,
    LOGISTICS_ROUTE_ACTIVE,
    LOGISTICS_ROUTE_DRAFT,
    LOGISTICS_ROUTE_OPTIMIZED,
    LOGISTICS_VEHICLE_AVAILABLE,
    LOGISTICS_VEHICLE_IN_USE,
)
from app.extensions.db import db
from app.models.logistics_driver import DriverProfile, Vehicle
from app.models.logistics_route import (
    DispatchAssignment,
    ETAEstimate,
    RoutePlan,
    RouteStop,
)
from app.models.logistics_tracking import ChainOfCustodyEvent, DeliveryProof, GPSPing
from app.services.crm_helpers import generate_code, get_or_404, list_resource
from app.services.route_optimizer import calculate_route_distance, estimate_minutes, haversine_km


class LogisticsError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class DriverService:
    @staticmethod
    def list_drivers(page=1, per_page=20, status=None, hub_city=None, q=None):
        filters = {"status": status, "hub_city": hub_city, "q": q}
        return list_resource(
            DriverProfile,
            lambda item: item.to_dict(),
            search_fields=["profile_code", "full_name", "phone", "email", "license_number"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_driver(data):
        profile = DriverProfile(
            profile_code=data.get("profile_code") or generate_code("DRV"),
            driver_id=data.get("driver_id"),
            full_name=data["full_name"],
            phone=data.get("phone"),
            email=data.get("email"),
            license_number=data.get("license_number"),
            hub_city=data.get("hub_city"),
            status=data.get("status", LOGISTICS_DRIVER_ACTIVE),
            rating=float(data.get("rating") or 5.0),
        )
        db.session.add(profile)
        db.session.commit()
        return profile

    @staticmethod
    def get_driver(profile_id):
        return get_or_404(DriverProfile, profile_id, LogisticsError).to_dict()


class VehicleService:
    @staticmethod
    def list_vehicles(page=1, per_page=20, status=None, vehicle_type=None, q=None):
        filters = {"status": status, "vehicle_type": vehicle_type, "q": q}
        return list_resource(
            Vehicle,
            lambda item: item.to_dict(),
            search_fields=["vehicle_code", "plate_number", "vehicle_type"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_vehicle(data):
        vehicle = Vehicle(
            vehicle_code=data.get("vehicle_code") or generate_code("VEH"),
            plate_number=data["plate_number"],
            vehicle_type=data.get("vehicle_type", "VAN"),
            capacity=int(data.get("capacity") or 20),
            status=data.get("status", LOGISTICS_VEHICLE_AVAILABLE),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
        )
        db.session.add(vehicle)
        db.session.commit()
        return vehicle

    @staticmethod
    def get_vehicle(vehicle_id):
        return get_or_404(Vehicle, vehicle_id, LogisticsError).to_dict()


class RouteOptimizationService:
    @staticmethod
    def list_routes(page=1, per_page=20, status=None, driver_profile_id=None, q=None):
        filters = {"status": status, "driver_profile_id": driver_profile_id, "q": q}
        return list_resource(
            RoutePlan,
            lambda item: item.to_dict(),
            search_fields=["route_code"],
            filters=filters,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    def create_route(data):
        route = RoutePlan(
            route_code=data.get("route_code") or generate_code("RTE"),
            driver_profile_id=data.get("driver_profile_id"),
            vehicle_id=data.get("vehicle_id"),
            status=data.get("status", LOGISTICS_ROUTE_DRAFT),
            start_latitude=data.get("start_latitude"),
            start_longitude=data.get("start_longitude"),
        )
        db.session.add(route)
        db.session.flush()
        stops_data = data.get("stops") or []
        for idx, stop_data in enumerate(stops_data):
            stop = RouteStop(
                route_plan_id=route.id,
                stop_sequence=int(stop_data.get("stop_sequence", idx + 1)),
                address=stop_data.get("address"),
                latitude=stop_data.get("latitude"),
                longitude=stop_data.get("longitude"),
                reference_type=stop_data.get("reference_type"),
                reference_id=stop_data.get("reference_id"),
            )
            db.session.add(stop)
        route.total_stops = len(stops_data)
        db.session.commit()
        return route

    @staticmethod
    def get_route(route_id):
        route = get_or_404(RoutePlan, route_id, LogisticsError)
        stops = (
            RouteStop.query.filter_by(route_plan_id=route.id)
            .order_by(RouteStop.stop_sequence.asc())
            .all()
        )
        payload = route.to_dict()
        payload["stops"] = [stop.to_dict() for stop in stops]
        return payload

    @staticmethod
    def _nearest_neighbor_order(start_lat, start_lon, stops):
        remaining = list(stops)
        ordered = []
        current_lat, current_lon = start_lat, start_lon
        while remaining:
            nearest = min(
                remaining,
                key=lambda s: haversine_km(
                    current_lat, current_lon, s.latitude or 0, s.longitude or 0
                ),
            )
            ordered.append(nearest)
            remaining.remove(nearest)
            current_lat = nearest.latitude or current_lat
            current_lon = nearest.longitude or current_lon
        return ordered

    @staticmethod
    def optimize_route(route_id):
        route = get_or_404(RoutePlan, route_id, LogisticsError)
        stops = RouteStop.query.filter_by(route_plan_id=route.id).all()
        if not stops:
            raise LogisticsError("Route has no stops", 400)

        start_lat = route.start_latitude or stops[0].latitude or 10.0452
        start_lon = route.start_longitude or stops[0].longitude or 105.7469
        ordered = RouteOptimizationService._nearest_neighbor_order(start_lat, start_lon, stops)

        points = [(start_lat, start_lon)]
        cumulative_minutes = 0
        now = datetime.utcnow()
        ETAEstimate.query.filter_by(route_plan_id=route.id).delete()

        for idx, stop in enumerate(ordered, start=1):
            stop.stop_sequence = idx
            if idx == 1:
                segment_km = haversine_km(
                    start_lat, start_lon, stop.latitude or start_lat, stop.longitude or start_lon
                )
            else:
                prev = ordered[idx - 2]
                segment_km = haversine_km(
                    prev.latitude or start_lat,
                    prev.longitude or start_lon,
                    stop.latitude or start_lat,
                    stop.longitude or start_lon,
                )
            segment_minutes = estimate_minutes(segment_km)
            cumulative_minutes += segment_minutes
            stop.eta_minutes = cumulative_minutes
            points.append((stop.latitude or start_lat, stop.longitude or start_lon))
            db.session.add(
                ETAEstimate(
                    route_plan_id=route.id,
                    route_stop_id=stop.id,
                    estimated_arrival=now + timedelta(minutes=cumulative_minutes),
                    estimated_minutes=cumulative_minutes,
                    confidence=0.85,
                )
            )

        route.total_distance_km = calculate_route_distance(points)
        route.estimated_minutes = cumulative_minutes
        route.total_stops = len(ordered)
        route.status = LOGISTICS_ROUTE_OPTIMIZED
        route.optimized_at = now
        db.session.commit()
        return RouteOptimizationService.get_route(route.id)


class DispatchBoardService:
    @staticmethod
    def get_board():
        pending = DispatchAssignment.query.filter_by(status=LOGISTICS_ASSIGNMENT_PENDING).count()
        assigned = DispatchAssignment.query.filter_by(status=LOGISTICS_ASSIGNMENT_ASSIGNED).count()
        active_routes = RoutePlan.query.filter_by(status=LOGISTICS_ROUTE_ACTIVE).count()
        available_drivers = DriverProfile.query.filter_by(status=LOGISTICS_DRIVER_ACTIVE).count()
        available_vehicles = Vehicle.query.filter_by(status=LOGISTICS_VEHICLE_AVAILABLE).count()

        assignments = (
            DispatchAssignment.query.order_by(DispatchAssignment.assigned_at.desc())
            .limit(20)
            .all()
        )
        routes = (
            RoutePlan.query.filter(
                RoutePlan.status.in_([LOGISTICS_ROUTE_OPTIMIZED, LOGISTICS_ROUTE_ACTIVE])
            )
            .order_by(RoutePlan.updated_at.desc())
            .limit(20)
            .all()
        )
        recent_pings = (
            GPSPing.query.order_by(GPSPing.recorded_at.desc()).limit(10).all()
        )

        return {
            "summary": {
                "pending_assignments": pending,
                "assigned_jobs": assigned,
                "active_routes": active_routes,
                "available_drivers": available_drivers,
                "available_vehicles": available_vehicles,
            },
            "assignments": [item.to_dict() for item in assignments],
            "routes": [item.to_dict() for item in routes],
            "recent_gps_pings": [item.to_dict() for item in recent_pings],
            "generated_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def assign(data):
        assignment = DispatchAssignment(
            assignment_code=data.get("assignment_code") or generate_code("ASN"),
            driver_profile_id=data.get("driver_profile_id"),
            vehicle_id=data.get("vehicle_id"),
            route_plan_id=data.get("route_plan_id"),
            status=LOGISTICS_ASSIGNMENT_ASSIGNED,
            priority=data.get("priority", "NORMAL"),
            reference_type=data.get("reference_type"),
            reference_id=data.get("reference_id"),
        )
        if assignment.driver_profile_id:
            driver = get_or_404(DriverProfile, assignment.driver_profile_id, LogisticsError)
            driver.active_vehicle_id = assignment.vehicle_id
        if assignment.vehicle_id:
            vehicle = get_or_404(Vehicle, assignment.vehicle_id, LogisticsError)
            vehicle.status = LOGISTICS_VEHICLE_IN_USE
            vehicle.current_driver_profile_id = assignment.driver_profile_id
        if assignment.route_plan_id:
            route = get_or_404(RoutePlan, assignment.route_plan_id, LogisticsError)
            route.driver_profile_id = assignment.driver_profile_id
            route.vehicle_id = assignment.vehicle_id
            route.status = LOGISTICS_ROUTE_ACTIVE
        db.session.add(assignment)
        db.session.flush()
        event = ChainOfCustodyEvent(
            event_code=generate_code("COC"),
            event_type=LOGISTICS_CUSTODY_PICKUP,
            reference_type="DISPATCH_ASSIGNMENT",
            reference_id=assignment.id,
            actor=data.get("actor", "SYSTEM"),
            location=data.get("location"),
        )
        db.session.add(event)
        db.session.commit()
        return assignment


class ETAService:
    @staticmethod
    def list_estimates(route_plan_id):
        rows = (
            ETAEstimate.query.filter_by(route_plan_id=route_plan_id)
            .order_by(ETAEstimate.estimated_minutes.asc())
            .all()
        )
        return {"count": len(rows), "estimates": [row.to_dict() for row in rows]}

    @staticmethod
    def recalculate(route_plan_id):
        return RouteOptimizationService.optimize_route(route_plan_id)


class ProofOfDeliveryService:
    @staticmethod
    def record_gps(data):
        ping = GPSPing(
            driver_profile_id=data.get("driver_profile_id"),
            vehicle_id=data.get("vehicle_id"),
            route_plan_id=data.get("route_plan_id"),
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            speed=float(data.get("speed") or 0),
            heading=float(data.get("heading") or 0),
        )
        if data.get("vehicle_id"):
            vehicle = Vehicle.query.get(data["vehicle_id"])
            if vehicle:
                vehicle.latitude = ping.latitude
                vehicle.longitude = ping.longitude
        db.session.add(ping)
        db.session.commit()
        return ping

    @staticmethod
    def record_proof(data):
        proof = DeliveryProof(
            assignment_id=data.get("assignment_id"),
            route_stop_id=data.get("route_stop_id"),
            proof_type=data.get("proof_type", "SIGNATURE"),
            proof_url=data.get("proof_url"),
            recipient_name=data.get("recipient_name"),
            captured_by=data.get("captured_by", "SYSTEM"),
        )
        db.session.add(proof)
        db.session.flush()
        if data.get("route_stop_id"):
            stop = RouteStop.query.get(data["route_stop_id"])
            if stop:
                stop.status = "COMPLETED"
        event = ChainOfCustodyEvent(
            event_code=generate_code("COC"),
            event_type=LOGISTICS_CUSTODY_DELIVERY,
            reference_type="DELIVERY_PROOF",
            reference_id=proof.id,
            actor=data.get("captured_by", "SYSTEM"),
            location=data.get("location"),
        )
        db.session.add(event)
        db.session.commit()
        return proof

    @staticmethod
    def list_proofs(page=1, per_page=20, assignment_id=None):
        filters = {"assignment_id": assignment_id, "q": None}
        return list_resource(
            DeliveryProof,
            lambda item: item.to_dict(),
            search_fields=["recipient_name", "proof_type"],
            filters=filters,
            page=page,
            per_page=per_page,
        )
