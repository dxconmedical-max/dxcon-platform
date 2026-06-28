import json
import math
from datetime import datetime

from app.core.audit import write_audit
from app.core.events import write_event
from app.core.qr_service import parse_qr_payload
from app.core.statuses import (
    ASSIGNMENT_ACCEPTED,
    ASSIGNMENT_ASSIGNED,
    CHECK_EVENT_CHECK_IN,
    CHECK_EVENT_CHECK_OUT,
    COLLECTOR_OPS_ON_DUTY,
    COLLECTOR_TIMELINE_BOX_UPDATE,
    COLLECTOR_TIMELINE_CHECK_IN,
    COLLECTOR_TIMELINE_CHECK_OUT,
    COLLECTOR_TIMELINE_GPS,
    COLLECTOR_TIMELINE_HANDOVER,
    COLLECTOR_TIMELINE_JOB_ACCEPTED,
    COLLECTOR_TIMELINE_OFFLINE_SYNC,
    COLLECTOR_TIMELINE_PICKUP,
    COLLECTOR_TIMELINE_PROOF,
    COLLECTOR_TIMELINE_QR_SCAN,
    COLLECTOR_TIMELINE_ROUTE_COMPLETED,
    COLLECTOR_TIMELINE_ROUTE_STARTED,
    HANDOVER_BOX,
    HANDOVER_SAMPLE,
    HANDOVER_SHIPMENT,
    OFFLINE_FAILED,
    OFFLINE_PENDING,
    OFFLINE_SYNCED,
    PROOF_PHOTO,
    PROOF_SIGNATURE,
    ROUTE_COMPLETED,
    ROUTE_IN_PROGRESS,
    ROUTE_OPTIMIZED,
    ROUTE_PLANNED,
    ROUTE_STOP_ARRIVED,
    ROUTE_STOP_COMPLETED,
    ROUTE_STOP_PENDING,
    SHIPMENT_CREATED,
    VALID_COLLECTOR_CHECK_EVENTS,
    VALID_COLLECTOR_TIMELINE_EVENTS,
    VALID_HANDOVER_TYPES,
    VALID_PROOF_TYPES,
    VEHICLE_ACTIVE,
)
from app.extensions.db import db
from app.models.booking_assignment import BookingAssignment
from app.models.collector_check_event import CollectorCheckEvent
from app.models.collector_gps_ping import CollectorGpsPing
from app.models.collector_handover import CollectorHandover
from app.models.collector_offline_sync import CollectorOfflineSync
from app.models.collector_operation_timeline import CollectorOperationTimeline
from app.models.collector_proof import CollectorProof
from app.models.collector_route import CollectorRoute
from app.models.collector_route_stop import CollectorRouteStop
from app.models.collector_vehicle import CollectorVehicle
from app.models.driver import Driver
from app.models.marketplace_booking import MarketplaceBooking
from app.models.sample_tracking import SampleTracking
from app.models.shipment import Shipment
from app.models.transport_box import TransportBox
from app.services.collector_workflow import (
    CollectorWorkflowError,
    accept_shipment,
    find_shipment,
    resolve_gps,
    start_trip,
)
from app.services.order_lifecycle import OrderLifecycleService
from app.services.sample_collection_workflow import SampleCollectionWorkflowService


class CollectorOperationsError(Exception):

    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class CollectorOperationsService:

    @staticmethod
    def _get_collector_or_raise(collector_id):
        collector = Driver.query.get(collector_id)
        if not collector:
            raise CollectorOperationsError("Collector not found", 404)
        return collector

    @staticmethod
    def _write_timeline(
        collector_id,
        event_type,
        message=None,
        route_id=None,
        booking_id=None,
        actor_email="SYSTEM",
        metadata=None,
    ):
        if event_type not in VALID_COLLECTOR_TIMELINE_EVENTS:
            raise CollectorOperationsError(
                f"Invalid timeline event. Must be one of: {', '.join(VALID_COLLECTOR_TIMELINE_EVENTS)}"
            )

        timeline = CollectorOperationTimeline(
            collector_id=collector_id,
            route_id=route_id,
            booking_id=booking_id,
            event_type=event_type,
            message=message,
            actor_email=actor_email,
            metadata_json=json.dumps(metadata) if metadata else None,
        )
        db.session.add(timeline)
        return timeline

    @staticmethod
    def get_profile(collector_id):
        collector = CollectorOperationsService._get_collector_or_raise(collector_id)
        vehicles = CollectorVehicle.query.filter_by(collector_id=collector_id).all()
        payload = collector.to_dict()
        payload["vehicles"] = [vehicle.to_dict() for vehicle in vehicles]
        return payload

    @staticmethod
    def update_profile(collector_id, data):
        collector = CollectorOperationsService._get_collector_or_raise(collector_id)

        for field in (
            "full_name",
            "phone",
            "email",
            "license_number",
            "home_city",
            "vehicle_no",
            "ops_status",
        ):
            if field in data and data[field] is not None:
                setattr(collector, field, data[field])

        db.session.commit()
        return collector

    @staticmethod
    def list_collectors(status=None):
        query = Driver.query
        if status:
            query = query.filter(Driver.status == status)
        return query.order_by(Driver.full_name.asc()).all()

    @staticmethod
    def create_vehicle(collector_id, data):
        CollectorOperationsService._get_collector_or_raise(collector_id)

        plate_number = data.get("plate_number")
        if not plate_number:
            raise CollectorOperationsError("plate_number is required")

        count = CollectorVehicle.query.count()
        vehicle = CollectorVehicle(
            vehicle_code=data.get("vehicle_code") or f"VEH-{count + 1:05d}",
            collector_id=collector_id,
            plate_number=plate_number,
            vehicle_type=data.get("vehicle_type", "MOTORBIKE"),
            brand=data.get("brand"),
            model=data.get("model"),
            capacity_boxes=int(data.get("capacity_boxes", 1)),
            status=data.get("status", VEHICLE_ACTIVE),
        )
        db.session.add(vehicle)
        db.session.commit()
        return vehicle

    @staticmethod
    def list_vehicles(collector_id=None):
        query = CollectorVehicle.query
        if collector_id:
            query = query.filter_by(collector_id=collector_id)
        return query.order_by(CollectorVehicle.created_at.desc()).all()

    @staticmethod
    def assign_active_vehicle(collector_id, vehicle_id):
        collector = CollectorOperationsService._get_collector_or_raise(collector_id)
        vehicle = CollectorVehicle.query.get(vehicle_id)
        if not vehicle or vehicle.collector_id != collector_id:
            raise CollectorOperationsError("Vehicle not found for collector", 404)

        collector.active_vehicle_id = vehicle.id
        collector.vehicle_no = vehicle.plate_number
        db.session.commit()
        return collector, vehicle

    @staticmethod
    def list_jobs(collector_id, status=None):
        CollectorOperationsService._get_collector_or_raise(collector_id)
        query = BookingAssignment.query.filter_by(collector_id=collector_id)

        if status:
            query = query.filter(BookingAssignment.assignment_status == status)

        assignments = query.order_by(BookingAssignment.created_at.desc()).all()
        jobs = []
        for assignment in assignments:
            booking = MarketplaceBooking.query.get(assignment.booking_id)
            if not booking:
                continue
            jobs.append(
                {
                    "assignment": assignment.to_dict(),
                    "booking": booking.to_dict(),
                    "order": (
                        OrderLifecycleService.get_order_for_booking(booking.id).to_dict()
                        if OrderLifecycleService.get_order_for_booking(booking.id)
                        else None
                    ),
                }
            )
        return jobs

    @staticmethod
    def accept_assignment(
        assignment_id,
        collector_id,
        actor_email="SYSTEM",
        ip_address="",
    ):
        assignment = BookingAssignment.query.get(assignment_id)
        if not assignment:
            raise CollectorOperationsError("Assignment not found", 404)

        if assignment.collector_id != collector_id:
            raise CollectorOperationsError("Assignment does not belong to collector", 403)

        if assignment.assignment_status not in (ASSIGNMENT_ASSIGNED, ASSIGNMENT_ACCEPTED):
            raise CollectorOperationsError(
                f"Assignment cannot be accepted from status {assignment.assignment_status}",
                409,
            )

        assignment.assignment_status = ASSIGNMENT_ACCEPTED
        assignment.accepted_at = datetime.utcnow()
        assignment.updated_at = datetime.utcnow()

        collector = CollectorOperationsService._get_collector_or_raise(collector_id)
        collector.ops_status = COLLECTOR_OPS_ON_DUTY

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_JOB_ACCEPTED,
            message=f"Collector accepted assignment {assignment.id}",
            booking_id=assignment.booking_id,
            actor_email=actor_email,
        )

        write_audit(
            action="COLLECTOR_ASSIGNMENT_ACCEPTED",
            object_type="BookingAssignment",
            object_id=assignment.id,
            user_email=actor_email,
            ip_address=ip_address,
        )
        write_event(
            event_type="COLLECTOR_ASSIGNMENT_ACCEPTED",
            object_type="BookingAssignment",
            object_id=assignment.id,
            message=f"Collector {collector_id} accepted assignment",
        )

        db.session.commit()
        return assignment

    @staticmethod
    def _haversine_km(lat1, lon1, lat2, lon2):
        try:
            lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        except (TypeError, ValueError):
            return 0.0

        radius = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return radius * (2 * math.asin(math.sqrt(a)))

    @staticmethod
    def create_route(collector_id, assignment_ids=None, transport_box_id=None):
        collector = CollectorOperationsService._get_collector_or_raise(collector_id)

        query = BookingAssignment.query.filter_by(
            collector_id=collector_id,
            assignment_status=ASSIGNMENT_ACCEPTED,
        )
        if assignment_ids:
            query = query.filter(BookingAssignment.id.in_(assignment_ids))

        assignments = query.all()
        if not assignments:
            raise CollectorOperationsError("No accepted assignments available for route", 409)

        count = CollectorRoute.query.count()
        route = CollectorRoute(
            route_code=f"RT-{count + 1:05d}",
            collector_id=collector_id,
            vehicle_id=collector.active_vehicle_id,
            transport_box_id=transport_box_id,
            status=ROUTE_PLANNED,
            total_stops=len(assignments),
        )
        db.session.add(route)
        db.session.flush()

        for index, assignment in enumerate(assignments, start=1):
            booking = MarketplaceBooking.query.get(assignment.booking_id)
            db.session.add(
                CollectorRouteStop(
                    route_id=route.id,
                    booking_id=assignment.booking_id,
                    assignment_id=assignment.id,
                    sequence_no=index,
                    patient_name=booking.patient_name if booking else None,
                    address=booking.patient_address if booking else None,
                    latitude=data_lat(booking),
                    longitude=data_lng(booking),
                    status=ROUTE_STOP_PENDING,
                )
            )

        db.session.commit()
        return route

    @staticmethod
    def optimize_route(route_id):
        route = CollectorRoute.query.get(route_id)
        if not route:
            raise CollectorOperationsError("Route not found", 404)

        stops = CollectorRouteStop.query.filter_by(route_id=route.id).order_by(
            CollectorRouteStop.sequence_no.asc()
        ).all()

        if len(stops) <= 1:
            route.status = ROUTE_OPTIMIZED
            route.optimized_at = datetime.utcnow()
            db.session.commit()
            return route, stops

        remaining = stops[:]
        ordered = []
        current = remaining.pop(0)
        ordered.append(current)
        total_distance = 0.0

        while remaining:
            current_lat = current.latitude or "0"
            current_lng = current.longitude or "0"
            nearest = min(
                remaining,
                key=lambda stop: CollectorOperationsService._haversine_km(
                    current_lat,
                    current_lng,
                    stop.latitude or current_lat,
                    stop.longitude or current_lng,
                ),
            )
            total_distance += CollectorOperationsService._haversine_km(
                current_lat,
                current_lng,
                nearest.latitude or current_lat,
                nearest.longitude or current_lng,
            )
            remaining.remove(nearest)
            ordered.append(nearest)
            current = nearest

        for index, stop in enumerate(ordered, start=1):
            stop.sequence_no = index

        route.total_distance_km = round(total_distance, 2)
        route.estimated_minutes = max(int(total_distance * 4), len(ordered) * 15)
        route.route_score = max(60.0, 100.0 - (total_distance * 0.5))
        route.status = ROUTE_OPTIMIZED
        route.optimized_at = datetime.utcnow()
        route.updated_at = datetime.utcnow()

        db.session.commit()
        return route, ordered

    @staticmethod
    def start_route(route_id, latitude=None, longitude=None, actor_email="SYSTEM"):
        route = CollectorRoute.query.get(route_id)
        if not route:
            raise CollectorOperationsError("Route not found", 404)

        if route.status not in (ROUTE_PLANNED, ROUTE_OPTIMIZED):
            raise CollectorOperationsError(
                f"Route cannot start from status {route.status}",
                409,
            )

        route.status = ROUTE_IN_PROGRESS
        route.started_at = datetime.utcnow()
        route.start_latitude = latitude
        route.start_longitude = longitude
        route.updated_at = datetime.utcnow()

        CollectorOperationsService._write_timeline(
            route.collector_id,
            COLLECTOR_TIMELINE_ROUTE_STARTED,
            message=f"Route {route.route_code} started",
            route_id=route.id,
            actor_email=actor_email,
        )

        db.session.commit()
        return route

    @staticmethod
    def complete_route(route_id, actor_email="SYSTEM"):
        route = CollectorRoute.query.get(route_id)
        if not route:
            raise CollectorOperationsError("Route not found", 404)

        route.status = ROUTE_COMPLETED
        route.completed_at = datetime.utcnow()
        route.completed_stops = route.total_stops
        route.updated_at = datetime.utcnow()

        stops = CollectorRouteStop.query.filter_by(route_id=route.id).all()
        for stop in stops:
            if stop.status != ROUTE_STOP_COMPLETED:
                stop.status = ROUTE_STOP_COMPLETED
                stop.completed_at = datetime.utcnow()

        CollectorOperationsService._write_timeline(
            route.collector_id,
            COLLECTOR_TIMELINE_ROUTE_COMPLETED,
            message=f"Route {route.route_code} completed",
            route_id=route.id,
            actor_email=actor_email,
        )

        db.session.commit()
        return route

    @staticmethod
    def get_route_detail(route_id):
        route = CollectorRoute.query.get(route_id)
        if not route:
            raise CollectorOperationsError("Route not found", 404)

        stops = CollectorRouteStop.query.filter_by(route_id=route.id).order_by(
            CollectorRouteStop.sequence_no.asc()
        ).all()
        payload = route.to_dict()
        payload["stops"] = [stop.to_dict() for stop in stops]
        return payload

    @staticmethod
    def list_routes(collector_id=None, status=None):
        query = CollectorRoute.query
        if collector_id:
            query = query.filter_by(collector_id=collector_id)
        if status:
            query = query.filter(CollectorRoute.status == status)
        return query.order_by(CollectorRoute.created_at.desc()).all()

    @staticmethod
    def record_check_event(
        collector_id,
        event_type,
        booking_id=None,
        route_id=None,
        latitude=None,
        longitude=None,
        note=None,
        actor_email="SYSTEM",
    ):
        if event_type not in VALID_COLLECTOR_CHECK_EVENTS:
            raise CollectorOperationsError(
                f"Invalid check event. Must be one of: {', '.join(VALID_COLLECTOR_CHECK_EVENTS)}"
            )

        CollectorOperationsService._get_collector_or_raise(collector_id)

        event = CollectorCheckEvent(
            collector_id=collector_id,
            route_id=route_id,
            booking_id=booking_id,
            event_type=event_type,
            latitude=latitude,
            longitude=longitude,
            note=note,
        )
        db.session.add(event)

        timeline_type = (
            COLLECTOR_TIMELINE_CHECK_IN
            if event_type == CHECK_EVENT_CHECK_IN
            else COLLECTOR_TIMELINE_CHECK_OUT
        )
        CollectorOperationsService._write_timeline(
            collector_id,
            timeline_type,
            message=note or f"Collector {event_type.lower().replace('_', ' ')}",
            route_id=route_id,
            booking_id=booking_id,
            actor_email=actor_email,
        )

        if booking_id and event_type == CHECK_EVENT_CHECK_IN:
            if OrderLifecycleService.get_order_for_booking(booking_id):
                SampleCollectionWorkflowService.check_in_collection(
                    booking_id,
                    actor_email=actor_email,
                )
                return event

        db.session.commit()
        return event

    @staticmethod
    def pickup_sample(
        booking_id,
        collector_id,
        latitude=None,
        longitude=None,
        note=None,
        actor_email="SYSTEM",
        ip_address="",
    ):
        CollectorOperationsService._get_collector_or_raise(collector_id)
        collection, sample = SampleCollectionWorkflowService.record_collection(
            booking_id,
            collector_id=collector_id,
            note=note,
            latitude=latitude,
            longitude=longitude,
            actor_email=actor_email,
            ip_address=ip_address,
        )

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_PICKUP,
            message=note or f"Sample picked up for booking {booking_id}",
            booking_id=booking_id,
            actor_email=actor_email,
        )

        stop = CollectorRouteStop.query.filter_by(booking_id=booking_id).first()
        if stop:
            stop.status = ROUTE_STOP_COMPLETED
            stop.completed_at = datetime.utcnow()

        db.session.commit()
        return collection, sample

    @staticmethod
    def record_gps_ping(
        collector_id,
        latitude,
        longitude,
        route_id=None,
        speed_kmh=None,
        heading=None,
        accuracy_m=None,
        actor_email="SYSTEM",
    ):
        if not latitude or not longitude:
            raise CollectorOperationsError("latitude and longitude are required")

        CollectorOperationsService._get_collector_or_raise(collector_id)

        ping = CollectorGpsPing(
            collector_id=collector_id,
            route_id=route_id,
            latitude=str(latitude),
            longitude=str(longitude),
            speed_kmh=speed_kmh,
            heading=heading,
            accuracy_m=accuracy_m,
            recorded_at=datetime.utcnow(),
        )
        db.session.add(ping)

        if route_id:
            route = CollectorRoute.query.get(route_id)
            if route and route.transport_box_id:
                box = TransportBox.query.get(route.transport_box_id)
                if box:
                    box.latitude = str(latitude)
                    box.longitude = str(longitude)
                    box.updated_at = datetime.utcnow()

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_GPS,
            message=f"GPS ping recorded at {latitude},{longitude}",
            route_id=route_id,
            actor_email=actor_email,
            metadata={"latitude": latitude, "longitude": longitude},
        )

        db.session.commit()
        return ping

    @staticmethod
    def get_gps_trail(collector_id, route_id=None, limit=50):
        query = CollectorGpsPing.query.filter_by(collector_id=collector_id)
        if route_id:
            query = query.filter_by(route_id=route_id)
        return query.order_by(CollectorGpsPing.recorded_at.desc()).limit(limit).all()

    @staticmethod
    def scan_qr(qr_payload, collector_id=None, actor_email="SYSTEM"):
        parsed = parse_qr_payload(qr_payload)
        if not parsed["valid"]:
            raise CollectorOperationsError("Invalid QR payload", 400)

        result = {
            "qr_payload": qr_payload,
            "type": parsed["type"],
            "code": parsed["code"],
            "resolved": None,
        }

        if parsed["type"] == "SAMPLE":
            sample = SampleTracking.query.filter_by(sample_code=parsed["code"]).first()
            result["resolved"] = sample.to_dict() if sample else None
        elif parsed["type"] == "BOX":
            box = TransportBox.query.filter_by(box_code=parsed["code"]).first()
            result["resolved"] = box.to_dict() if box else None
        elif parsed["type"] == "SHIPMENT":
            shipment = find_shipment(parsed["code"])
            result["resolved"] = shipment.to_dict() if shipment else None

        if collector_id:
            CollectorOperationsService._write_timeline(
                collector_id,
                COLLECTOR_TIMELINE_QR_SCAN,
                message=f"QR scanned: {parsed['type']} {parsed['code']}",
                actor_email=actor_email,
            )
            db.session.commit()

        return result

    @staticmethod
    def create_handover(
        collector_id,
        handover_type,
        object_code,
        qr_payload=None,
        booking_id=None,
        recipient_name=None,
        latitude=None,
        longitude=None,
        note=None,
        actor_email="SYSTEM",
    ):
        if handover_type not in VALID_HANDOVER_TYPES:
            raise CollectorOperationsError(
                f"Invalid handover type. Must be one of: {', '.join(VALID_HANDOVER_TYPES)}"
            )

        CollectorOperationsService._get_collector_or_raise(collector_id)

        sample_tracking_id = None
        transport_box_id = None
        shipment_id = None

        if handover_type == HANDOVER_SAMPLE:
            sample = SampleTracking.query.filter_by(sample_code=object_code).first()
            if sample:
                sample_tracking_id = sample.id
                booking_id = booking_id or sample.marketplace_booking_id
        elif handover_type == HANDOVER_BOX:
            box = TransportBox.query.filter_by(box_code=object_code).first()
            if box:
                transport_box_id = box.id
        elif handover_type == HANDOVER_SHIPMENT:
            shipment = find_shipment(object_code)
            if shipment:
                shipment_id = shipment.id

        handover = CollectorHandover(
            collector_id=collector_id,
            handover_type=handover_type,
            object_code=object_code,
            qr_payload=qr_payload,
            booking_id=booking_id,
            sample_tracking_id=sample_tracking_id,
            transport_box_id=transport_box_id,
            shipment_id=shipment_id,
            recipient_name=recipient_name,
            latitude=latitude,
            longitude=longitude,
            note=note,
        )
        db.session.add(handover)

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_HANDOVER,
            message=note or f"{handover_type} handover recorded for {object_code}",
            booking_id=booking_id,
            actor_email=actor_email,
        )

        db.session.commit()
        return handover

    @staticmethod
    def update_cold_box(
        box_id,
        collector_id,
        temperature=None,
        battery_level=None,
        latitude=None,
        longitude=None,
        actor_email="SYSTEM",
    ):
        box = TransportBox.query.get(box_id)
        if not box:
            raise CollectorOperationsError("Transport box not found", 404)

        if temperature is not None:
            box.temperature = float(temperature)
        if battery_level is not None:
            box.battery_level = int(battery_level)
        if latitude is not None:
            box.latitude = str(latitude)
        if longitude is not None:
            box.longitude = str(longitude)

        box.update_alert_status()
        box.updated_at = datetime.utcnow()

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_BOX_UPDATE,
            message=f"Cold box {box.box_code} telemetry updated",
            actor_email=actor_email,
            metadata={
                "temperature": box.temperature,
                "battery_level": box.battery_level,
                "alert_status": box.alert_status,
            },
        )

        db.session.commit()
        return box

    @staticmethod
    def add_proof(
        collector_id,
        proof_type,
        booking_id=None,
        route_stop_id=None,
        file_name=None,
        content_base64=None,
        signer_name=None,
        note=None,
        actor_email="SYSTEM",
    ):
        if proof_type not in VALID_PROOF_TYPES:
            raise CollectorOperationsError(
                f"Invalid proof type. Must be one of: {', '.join(VALID_PROOF_TYPES)}"
            )

        CollectorOperationsService._get_collector_or_raise(collector_id)

        proof = CollectorProof(
            collector_id=collector_id,
            proof_type=proof_type,
            booking_id=booking_id,
            route_stop_id=route_stop_id,
            file_name=file_name,
            content_base64=content_base64,
            signer_name=signer_name,
            note=note,
        )
        db.session.add(proof)

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_PROOF,
            message=note or f"{proof_type} proof captured",
            booking_id=booking_id,
            actor_email=actor_email,
        )

        db.session.commit()
        return proof

    @staticmethod
    def queue_offline_event(collector_id, client_event_id, event_type, payload):
        if not client_event_id or not event_type:
            raise CollectorOperationsError("client_event_id and event_type are required")

        existing = CollectorOfflineSync.query.filter_by(
            collector_id=collector_id,
            client_event_id=client_event_id,
        ).first()
        if existing:
            return existing

        record = CollectorOfflineSync(
            collector_id=collector_id,
            client_event_id=client_event_id,
            event_type=event_type,
            payload_json=json.dumps(payload or {}),
            status=OFFLINE_PENDING,
            client_recorded_at=datetime.utcnow(),
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def sync_offline_events(collector_id, actor_email="SYSTEM"):
        pending = CollectorOfflineSync.query.filter_by(
            collector_id=collector_id,
            status=OFFLINE_PENDING,
        ).order_by(CollectorOfflineSync.created_at.asc()).all()

        synced = 0
        failed = 0
        for record in pending:
            try:
                payload = json.loads(record.payload_json or "{}")
                event_type = record.event_type

                if event_type == "GPS":
                    CollectorOperationsService.record_gps_ping(
                        collector_id,
                        payload.get("latitude"),
                        payload.get("longitude"),
                        route_id=payload.get("route_id"),
                        actor_email=actor_email,
                    )
                elif event_type == "CHECK_IN":
                    CollectorOperationsService.record_check_event(
                        collector_id,
                        CHECK_EVENT_CHECK_IN,
                        booking_id=payload.get("booking_id"),
                        route_id=payload.get("route_id"),
                        latitude=payload.get("latitude"),
                        longitude=payload.get("longitude"),
                        actor_email=actor_email,
                    )
                elif event_type == "PICKUP":
                    CollectorOperationsService.pickup_sample(
                        payload.get("booking_id"),
                        collector_id,
                        latitude=payload.get("latitude"),
                        longitude=payload.get("longitude"),
                        note=payload.get("note"),
                        actor_email=actor_email,
                    )
                elif event_type == "QR_SCAN":
                    CollectorOperationsService.scan_qr(
                        payload.get("qr_payload"),
                        collector_id=collector_id,
                        actor_email=actor_email,
                    )
                else:
                    raise CollectorOperationsError(f"Unsupported offline event {event_type}")

                record.status = OFFLINE_SYNCED
                record.synced_at = datetime.utcnow()
                synced += 1
            except Exception as exc:
                record.status = OFFLINE_FAILED
                record.error_message = str(exc)
                failed += 1

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_OFFLINE_SYNC,
            message=f"Offline sync completed: {synced} synced, {failed} failed",
            actor_email=actor_email,
            metadata={"synced": synced, "failed": failed},
        )

        db.session.commit()
        return {"synced": synced, "failed": failed, "pending": len(pending) - synced - failed}

    @staticmethod
    def list_timeline(collector_id, limit=50):
        return CollectorOperationTimeline.query.filter_by(
            collector_id=collector_id
        ).order_by(CollectorOperationTimeline.created_at.desc()).limit(limit).all()

    @staticmethod
    def accept_collector_shipment(
        shipment_id,
        collector_id,
        latitude=None,
        longitude=None,
        actor_email="SYSTEM",
    ):
        shipment = find_shipment(shipment_id)
        if not shipment:
            raise CollectorOperationsError("Shipment not found", 404)

        try:
            shipment = accept_shipment(
                shipment,
                collector_id=collector_id,
                gps_location=resolve_gps(latitude=latitude, longitude=longitude),
                actor=actor_email,
            )
        except CollectorWorkflowError as exc:
            raise CollectorOperationsError(exc.message, exc.status_code)

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_HANDOVER,
            message=f"Shipment {shipment.shipment_code} accepted",
            actor_email=actor_email,
        )
        db.session.commit()
        return shipment

    @staticmethod
    def start_collector_shipment_trip(
        shipment_id,
        collector_id,
        latitude=None,
        longitude=None,
        actor_email="SYSTEM",
    ):
        shipment = find_shipment(shipment_id)
        if not shipment:
            raise CollectorOperationsError("Shipment not found", 404)

        try:
            shipment = start_trip(
                shipment,
                collector_id=collector_id,
                gps_location=resolve_gps(latitude=latitude, longitude=longitude),
                actor=actor_email,
            )
        except CollectorWorkflowError as exc:
            raise CollectorOperationsError(exc.message, exc.status_code)

        CollectorOperationsService._write_timeline(
            collector_id,
            COLLECTOR_TIMELINE_ROUTE_STARTED,
            message=f"Shipment trip started for {shipment.shipment_code}",
            actor_email=actor_email,
        )
        db.session.commit()
        return shipment

    @staticmethod
    def collector_dashboard(collector_id):
        collector = CollectorOperationsService.get_profile(collector_id)
        jobs = CollectorOperationsService.list_jobs(collector_id)
        routes = CollectorOperationsService.list_routes(collector_id)
        timeline = CollectorOperationsService.list_timeline(collector_id, limit=20)
        gps_trail = CollectorOperationsService.get_gps_trail(collector_id, limit=10)

        active_route = next(
            (route for route in routes if route.status == ROUTE_IN_PROGRESS),
            None,
        )

        return {
            "collector": collector,
            "jobs_total": len(jobs),
            "jobs_pending": len(
                [job for job in jobs if job["assignment"]["assignment_status"] == ASSIGNMENT_ASSIGNED]
            ),
            "jobs_accepted": len(
                [job for job in jobs if job["assignment"]["assignment_status"] == ASSIGNMENT_ACCEPTED]
            ),
            "active_route": active_route.to_dict() if active_route else None,
            "routes_total": len(routes),
            "recent_timeline": [item.to_dict() for item in timeline],
            "recent_gps": [item.to_dict() for item in gps_trail],
        }

    @staticmethod
    def supervisor_dashboard():
        collectors = CollectorOperationsService.list_collectors(status="ACTIVE")
        routes = CollectorRoute.query.order_by(CollectorRoute.created_at.desc()).limit(20).all()
        boxes = TransportBox.query.order_by(TransportBox.updated_at.desc()).limit(20).all()
        alerts = [box.to_dict() for box in boxes if box.alert_status != "NORMAL"]
        pending_offline = CollectorOfflineSync.query.filter_by(status=OFFLINE_PENDING).count()

        return {
            "collectors_total": len(collectors),
            "collectors_on_duty": len(
                [collector for collector in collectors if collector.ops_status == COLLECTOR_OPS_ON_DUTY]
            ),
            "routes_active": len([route for route in routes if route.status == ROUTE_IN_PROGRESS]),
            "routes_total": len(routes),
            "cold_box_alerts": alerts,
            "offline_pending": pending_offline,
            "recent_routes": [route.to_dict() for route in routes[:10]],
        }


def data_lat(booking):
    return None


def data_lng(booking):
    return None
