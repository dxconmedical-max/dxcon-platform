"""Authoritative collection routing domain.

Modes: AT_RECEPTION | HOME_COLLECTION | CLINIC_COLLECTION
Canonical status machine with one-time legacy normalization at API boundaries.
"""

from __future__ import annotations

from typing import Any

# --- Modes (authoritative; never infer from source=desk / missing booking) ---

MODE_AT_RECEPTION = "AT_RECEPTION"
MODE_HOME_COLLECTION = "HOME_COLLECTION"
MODE_CLINIC_COLLECTION = "CLINIC_COLLECTION"

VALID_COLLECTION_MODES = frozenset(
    {MODE_AT_RECEPTION, MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION}
)
FIELD_COLLECTION_MODES = frozenset({MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION})
DESK_COLLECTION_MODES = frozenset({MODE_AT_RECEPTION})

# --- Canonical statuses ---

ST_DRAFT = "DRAFT"
ST_REQUESTED = "REQUESTED"
ST_ASSIGNED = "ASSIGNED"
ST_VERIFIED = "VERIFIED"
ST_COLLECTED = "COLLECTED"
ST_IN_TRANSIT = "IN_TRANSIT"
ST_ARRIVED_AT_LAB = "ARRIVED_AT_LAB"
ST_RECEIVED = "RECEIVED"
ST_ACCESSIONED = "ACCESSIONED"
ST_PROCESSING = "PROCESSING"
ST_RESULTED = "RESULTED"
ST_TECHNICALLY_VALIDATED = "TECHNICALLY_VALIDATED"
ST_MEDICALLY_VALIDATED = "MEDICALLY_VALIDATED"
ST_RELEASED = "RELEASED"
ST_CANCELLED = "CANCELLED"
ST_REJECTED = "REJECTED"
ST_RECOLLECT_REQUIRED = "RECOLLECT_REQUIRED"

CANONICAL_STATUSES = (
    ST_DRAFT,
    ST_REQUESTED,
    ST_ASSIGNED,
    ST_VERIFIED,
    ST_COLLECTED,
    ST_IN_TRANSIT,
    ST_ARRIVED_AT_LAB,
    ST_RECEIVED,
    ST_ACCESSIONED,
    ST_PROCESSING,
    ST_RESULTED,
    ST_TECHNICALLY_VALIDATED,
    ST_MEDICALLY_VALIDATED,
    ST_RELEASED,
    ST_CANCELLED,
    ST_REJECTED,
    ST_RECOLLECT_REQUIRED,
)

# One-time legacy → canonical map (API boundary only)
LEGACY_STATUS_TO_CANONICAL: dict[str, str] = {
    "PENDING": ST_REQUESTED,
    "pending": ST_REQUESTED,
    "ASSIGNED": ST_ASSIGNED,
    "assigned": ST_ASSIGNED,
    "AWAITING_COLLECTION": ST_REQUESTED,
    "CHECKED_IN": ST_VERIFIED,
    "accepted": ST_VERIFIED,
    "VERIFIED": ST_VERIFIED,
    "COLLECTED": ST_COLLECTED,
    "collected": ST_COLLECTED,
    "IN_TRANSIT": ST_IN_TRANSIT,
    "in_transit": ST_IN_TRANSIT,
    "RECEIVED": ST_ARRIVED_AT_LAB,  # historical collector lab-arrival label
    "received": ST_ARRIVED_AT_LAB,
    "delivered": ST_ARRIVED_AT_LAB,
    "ARRIVED_AT_LAB": ST_ARRIVED_AT_LAB,
    "REJECTED": ST_REJECTED,
    "rejected": ST_REJECTED,
    "RECOLLECT_REQUIRED": ST_RECOLLECT_REQUIRED,
    "CANCELLED": ST_CANCELLED,
    "cancelled": ST_CANCELLED,
}

# Desk awaiting / field awaiting (canonical stored values + safe legacy)
DESK_QUEUE_STATUSES = frozenset(
    {ST_REQUESTED, ST_ASSIGNED, ST_VERIFIED, ST_RECOLLECT_REQUIRED, "PENDING", "CHECKED_IN"}
)
FIELD_QUEUE_STATUSES = frozenset(
    {
        ST_REQUESTED,
        ST_ASSIGNED,
        ST_VERIFIED,
        ST_RECOLLECT_REQUIRED,
        "PENDING",
        "CHECKED_IN",
        "assigned",
    }
)

# Allowed transitions (from → to)
TRANSITIONS: dict[str, frozenset[str]] = {
    ST_DRAFT: frozenset({ST_REQUESTED, ST_CANCELLED}),
    ST_REQUESTED: frozenset({ST_ASSIGNED, ST_VERIFIED, ST_CANCELLED, ST_REJECTED}),
    ST_ASSIGNED: frozenset({ST_VERIFIED, ST_CANCELLED, ST_REJECTED, ST_RECOLLECT_REQUIRED}),
    ST_VERIFIED: frozenset({ST_COLLECTED, ST_REJECTED, ST_RECOLLECT_REQUIRED, ST_CANCELLED}),
    ST_COLLECTED: frozenset({ST_IN_TRANSIT, ST_ARRIVED_AT_LAB, ST_REJECTED, ST_RECOLLECT_REQUIRED}),
    ST_IN_TRANSIT: frozenset({ST_ARRIVED_AT_LAB, ST_REJECTED}),
    ST_ARRIVED_AT_LAB: frozenset({ST_RECEIVED, ST_REJECTED}),
    ST_RECEIVED: frozenset({ST_ACCESSIONED, ST_REJECTED}),
    ST_ACCESSIONED: frozenset({ST_PROCESSING, ST_REJECTED}),
    ST_PROCESSING: frozenset({ST_RESULTED, ST_REJECTED}),
    ST_RESULTED: frozenset({ST_TECHNICALLY_VALIDATED, ST_REJECTED}),
    ST_TECHNICALLY_VALIDATED: frozenset({ST_MEDICALLY_VALIDATED, ST_REJECTED}),
    ST_MEDICALLY_VALIDATED: frozenset({ST_RELEASED}),
    ST_RELEASED: frozenset(),
    ST_CANCELLED: frozenset(),
    ST_REJECTED: frozenset({ST_RECOLLECT_REQUIRED}),
    ST_RECOLLECT_REQUIRED: frozenset({ST_REQUESTED, ST_ASSIGNED, ST_CANCELLED}),
}


class CollectionDomainError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def normalize_status(status: str | None) -> str:
    """Single API-boundary normalizer for legacy + canonical statuses."""
    if not status:
        return ST_REQUESTED
    raw = str(status).strip()
    # Legacy aliases first (e.g. PENDING→REQUESTED, CHECKED_IN→VERIFIED, delivered→ARRIVED_AT_LAB)
    if raw in LEGACY_STATUS_TO_CANONICAL:
        return LEGACY_STATUS_TO_CANONICAL[raw]
    if raw in CANONICAL_STATUSES:
        return raw
    upper = raw.upper()
    if upper in LEGACY_STATUS_TO_CANONICAL:
        return LEGACY_STATUS_TO_CANONICAL[upper]
    if upper in CANONICAL_STATUSES:
        return upper
    return upper


def assert_transition(current: str | None, target: str) -> str:
    """Validate transition; raise CollectionDomainError(409) if invalid."""
    from_status = normalize_status(current)
    to_status = normalize_status(target)
    allowed = TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise CollectionDomainError(
            f"Invalid collection transition: {from_status} → {to_status}",
            409,
        )
    return to_status


def validate_mode(mode: str | None) -> str:
    value = (mode or "").strip().upper()
    if value not in VALID_COLLECTION_MODES:
        raise CollectionDomainError(
            "collection_mode is required and must be one of: "
            + ", ".join(sorted(VALID_COLLECTION_MODES)),
            400,
        )
    return value


def is_field_mode(mode: str | None) -> bool:
    return (mode or "").strip().upper() in FIELD_COLLECTION_MODES


def is_desk_mode(mode: str | None) -> bool:
    return (mode or "").strip().upper() == MODE_AT_RECEPTION


def validate_pickup_details(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Require pickup fields for HOME/CLINIC; ignore for AT_RECEPTION."""
    if mode == MODE_AT_RECEPTION:
        return {}
    required = ("pickup_address", "pickup_city", "contact_phone", "requested_date", "requested_time_window")
    missing = [key for key in required if not str(payload.get(key) or "").strip()]
    if missing:
        raise CollectionDomainError(
            f"Field collection requires: {', '.join(missing)}",
            400,
        )
    return {
        "pickup_address": str(payload["pickup_address"]).strip(),
        "pickup_city": str(payload["pickup_city"]).strip(),
        "contact_phone": str(payload["contact_phone"]).strip(),
        "requested_date": str(payload["requested_date"]).strip(),
        "requested_time_window": str(payload["requested_time_window"]).strip(),
        "collection_request_note": (str(payload.get("note") or payload.get("collection_request_note") or "").strip() or None),
        "pickup_latitude": (str(payload.get("latitude") or payload.get("pickup_latitude") or "").strip() or None),
        "pickup_longitude": (str(payload.get("longitude") or payload.get("pickup_longitude") or "").strip() or None),
    }


def infer_legacy_mode(row: dict[str, Any] | Any) -> tuple[str | None, str]:
    """Deterministic legacy mapping for backfill/reporting. Never silently guess clinic vs home without booking.

    Returns (mode_or_None, reason).
    """
    if isinstance(row, dict):
        notes = str(row.get("notes") or "")
        location = str(row.get("collection_location") or "")
        collector = str(row.get("collector_name") or "")
        booking = row.get("marketplace_booking_id")
        existing = row.get("collection_mode")
    else:
        notes = str(getattr(row, "notes", None) or "")
        location = str(getattr(row, "collection_location", None) or "")
        collector = str(getattr(row, "collector_name", None) or "")
        booking = getattr(row, "marketplace_booking_id", None)
        existing = getattr(row, "collection_mode", None)

    if existing and str(existing).strip().upper() in VALID_COLLECTION_MODES:
        return str(existing).strip().upper(), "already_set"

    if "source:desk" in notes or location.lower() == "reception desk" or collector.lower() == "walk-in collector":
        return MODE_AT_RECEPTION, "desk_markers"

    if booking:
        return MODE_HOME_COLLECTION, "marketplace_booking_id"

    return None, "ambiguous"


def workflow_path_for_mode(mode: str) -> str:
    if mode == MODE_AT_RECEPTION:
        return "/app/reception/desk-collections"
    return "/app/collector/workflow"
