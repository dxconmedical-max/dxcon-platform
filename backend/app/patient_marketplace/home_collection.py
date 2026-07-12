"""Home collection — saved addresses, GPS, distance, collector instructions."""

from __future__ import annotations

import uuid
from typing import Any

from app.extensions.db import db
from app.patient_marketplace.models import MpPatientAddress
from app.patient_marketplace.service import MarketplaceError, _haversine_km


class HomeCollectionService:
    @staticmethod
    def list_addresses(patient_user_id: str, *, organization_id: str) -> dict:
        rows = MpPatientAddress.query.filter_by(
            patient_user_id=patient_user_id,
            organization_id=organization_id,
        ).order_by(MpPatientAddress.is_default.desc(), MpPatientAddress.created_at.desc()).all()
        return {"count": len(rows), "addresses": [r.to_dict() for r in rows]}

    @staticmethod
    def save_address(data: dict, *, organization_id: str, patient_user_id: str) -> dict:
        if data.get("is_default"):
            MpPatientAddress.query.filter_by(
                patient_user_id=patient_user_id,
                organization_id=organization_id,
            ).update({"is_default": False})
        row = MpPatientAddress(
            organization_id=organization_id,
            patient_user_id=patient_user_id,
            label=data.get("label", "Home"),
            address_line=data["address_line"],
            building=data.get("building"),
            apartment=data.get("apartment"),
            city=data.get("city"),
            district=data.get("district"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            contact_instructions=data.get("contact_instructions"),
            collector_notes=data.get("collector_notes"),
            preferred_window_start=data.get("preferred_window_start"),
            preferred_window_end=data.get("preferred_window_end"),
            is_default=bool(data.get("is_default")),
        )
        db.session.add(row)
        db.session.flush()
        return row.to_dict()

    @staticmethod
    def distance_to_provider(address_id: str, provider_lat: float, provider_lng: float) -> dict:
        addr = MpPatientAddress.query.get(address_id)
        if not addr or addr.latitude is None or addr.longitude is None:
            raise MarketplaceError("Address coordinates required", 400)
        km = _haversine_km(addr.latitude, addr.longitude, provider_lat, provider_lng)
        return {"distance_km": km, "address_id": address_id}
