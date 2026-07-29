"""Authoritative collection routing domain.

Modes: AT_RECEPTION | HOME_COLLECTION | CLINIC_COLLECTION
UI aliases: DESK → AT_RECEPTION, HOME → HOME_COLLECTION, CLINIC → CLINIC_COLLECTION
Canonical status machine with one-time legacy normalization at API boundaries.
"""

from __future__ import annotations

from typing import Any

# --- Modes (authoritative; never infer from source=desk / missing booking) ---

MODE_AT_RECEPTION = "AT_RECEPTION"
MODE_HOME_COLLECTION = "HOME_COLLECTION"
MODE_CLINIC_COLLECTION = "CLINIC_COLLECTION"

MODE_ALIASES = {
    "DESK": MODE_AT_RECEPTION,
    "AT_RECEPTION": MODE_AT_RECEPTION,
    "RECEPTION": MODE_AT_RECEPTION,
    "HOME": MODE_HOME_COLLECTION,
    "HOME_COLLECTION": MODE_HOME_COLLECTION,
    "CLINIC": MODE_CLINIC_COLLECTION,
    "CLINIC_COLLECTION": MODE_CLINIC_COLLECTION,
}

VALID_COLLECTION_MODES = frozenset(
    {MODE_AT_RECEPTION, MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION}
)
FIELD_COLLECTION_MODES = frozenset({MODE_HOME_COLLECTION, MODE_CLINIC_COLLECTION})
DESK_COLLECTION_MODES = frozenset({MODE_AT_RECEPTION})

# --- Canonical statuses ---

ST_DRAFT = "DRAFT"
ST_REQUESTED = "REQUESTED"
ST_PENDING_ASSIGNMENT = "PENDING_ASSIGNMENT"
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
    ST_PENDING_ASSIGNMENT,
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
    "PENDING_ASSIGNMENT": ST_PENDING_ASSIGNMENT,
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
    "RECEIVED": ST_ARRIVED_AT_LAB,
    "received": ST_ARRIVED_AT_LAB,
    "delivered": ST_ARRIVED_AT_LAB,
    "ARRIVED_AT_LAB": ST_ARRIVED_AT_LAB,
    "REJECTED": ST_REJECTED,
    "rejected": ST_REJECTED,
    "RECOLLECT_REQUIRED": ST_RECOLLECT_REQUIRED,
    "CANCELLED": ST_CANCELLED,
    "cancelled": ST_CANCELLED,
}

DESK_QUEUE_STATUSES = frozenset(
    {ST_REQUESTED, ST_ASSIGNED, ST_VERIFIED, ST_RECOLLECT_REQUIRED, "PENDING", "CHECKED_IN"}
)
FIELD_QUEUE_STATUSES = frozenset(
    {
        ST_PENDING_ASSIGNMENT,
        ST_REQUESTED,
        ST_ASSIGNED,
        ST_VERIFIED,
        ST_RECOLLECT_REQUIRED,
        "PENDING",
        "CHECKED_IN",
        "assigned",
    }
)

TRANSITIONS: dict[str, frozenset[str]] = {
    ST_DRAFT: frozenset({ST_REQUESTED, ST_PENDING_ASSIGNMENT, ST_CANCELLED}),
    ST_REQUESTED: frozenset(
        {ST_PENDING_ASSIGNMENT, ST_ASSIGNED, ST_VERIFIED, ST_CANCELLED, ST_REJECTED}
    ),
    ST_PENDING_ASSIGNMENT: frozenset({ST_ASSIGNED, ST_CANCELLED, ST_REJECTED}),
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
    ST_RECOLLECT_REQUIRED: frozenset({ST_REQUESTED, ST_PENDING_ASSIGNMENT, ST_ASSIGNED, ST_CANCELLED}),
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
    raw = (mode or "").strip().upper()
    value = MODE_ALIASES.get(raw, raw)
    if value not in VALID_COLLECTION_MODES:
        raise CollectionDomainError(
            "collection_mode is required and must be one of: "
            "DESK/AT_RECEPTION, HOME/HOME_COLLECTION, CLINIC/CLINIC_COLLECTION",
            400,
        )
    return value


def is_field_mode(mode: str | None) -> bool:
    try:
        return validate_mode(mode) in FIELD_COLLECTION_MODES
    except CollectionDomainError:
        return False


def is_desk_mode(mode: str | None) -> bool:
    try:
        return validate_mode(mode) == MODE_AT_RECEPTION
    except CollectionDomainError:
        return False


def _strip(value: Any) -> str:
    return str(value or "").strip()


def validate_collection_request(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate mode-specific Collection Request fields before order create."""
    mode = validate_mode(mode)
    specimen_type = _strip(payload.get("specimen_type")) or "BLOOD"
    notes = _strip(payload.get("notes") or payload.get("note") or payload.get("collection_request_note")) or None
    priority = _strip(payload.get("priority")) or None

    if mode == MODE_AT_RECEPTION:
        if not specimen_type:
            raise CollectionDomainError("DESK collection requires specimen_type", 400)
        return {
            "specimen_type": specimen_type,
            "collection_request_note": notes,
            "priority": priority,
        }

    if mode == MODE_HOME_COLLECTION:
        required = {
            "pickup_address": _strip(payload.get("pickup_address")),
            "pickup_province": _strip(payload.get("pickup_province") or payload.get("province")),
            "pickup_district": _strip(payload.get("pickup_district") or payload.get("district")),
            "contact_person": _strip(payload.get("contact_person")),
            "contact_phone": _strip(payload.get("contact_phone") or payload.get("phone")),
            "requested_date": _strip(payload.get("requested_date")),
            "requested_time_window": _strip(
                payload.get("requested_time_window") or payload.get("time_window")
            ),
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise CollectionDomainError(
                f"HOME collection requires: {', '.join(missing)}",
                400,
            )
        province = required["pickup_province"]
        district = required["pickup_district"]
        ward = _strip(payload.get("pickup_ward") or payload.get("ward")) or None
        city = _strip(payload.get("pickup_city")) or ", ".join(
            part for part in (district, province) if part
        )
        return {
            "specimen_type": specimen_type,
            "pickup_address": required["pickup_address"],
            "pickup_province": province,
            "pickup_district": district,
            "pickup_ward": ward,
            "pickup_city": city,
            "contact_person": required["contact_person"],
            "contact_phone": required["contact_phone"],
            "requested_date": required["requested_date"],
            "requested_time_window": required["requested_time_window"],
            "collection_request_note": notes,
            "priority": priority or "ROUTINE",
            "pickup_latitude": _strip(payload.get("latitude") or payload.get("pickup_latitude")) or None,
            "pickup_longitude": _strip(payload.get("longitude") or payload.get("pickup_longitude")) or None,
        }

    # CLINIC_COLLECTION
    clinic_name = _strip(
        payload.get("clinic_name") or payload.get("clinic") or payload.get("pickup_address")
    )
    requested_date = _strip(payload.get("requested_date"))
    requested_time = _strip(
        payload.get("requested_time_window")
        or payload.get("preferred_time")
        or payload.get("time_window")
    )
    if not clinic_name:
        raise CollectionDomainError("CLINIC collection requires clinic name", 400)
    if not requested_date:
        raise CollectionDomainError("CLINIC collection requires preferred date", 400)
    if not requested_time:
        raise CollectionDomainError("CLINIC collection requires preferred time", 400)
    return {
        "specimen_type": specimen_type,
        "clinic_name": clinic_name,
        "pickup_address": clinic_name,
        "pickup_city": _strip(payload.get("pickup_city")) or clinic_name,
        "contact_person": _strip(payload.get("contact_person")) or None,
        "contact_phone": _strip(payload.get("contact_phone") or payload.get("phone")) or None,
        "requested_date": requested_date,
        "requested_time_window": requested_time,
        "collection_request_note": notes,
        "priority": priority or "ROUTINE",
    }


# Back-compat name used by earlier modules
def validate_pickup_details(mode: str, payload: dict[str, Any]) -> dict[str, Any]:
    return validate_collection_request(mode, payload)


def initial_status_for_mode(mode: str) -> str:
    mode = validate_mode(mode)
    if mode in FIELD_COLLECTION_MODES:
        return ST_PENDING_ASSIGNMENT
    return ST_REQUESTED


def infer_legacy_mode(row: dict[str, Any] | Any) -> tuple[str | None, str]:
    """Deterministic legacy mapping. Ambiguous rows stay None (reported, not guessed)."""
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
    if validate_mode(mode) == MODE_AT_RECEPTION:
        return "/app/reception/desk-collections"
    return "/app/collector/workflow"
