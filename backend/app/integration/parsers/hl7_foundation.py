"""HL7 v2 foundation parser — Epic 3.5 (subset, not certified)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

SUPPORTED_MESSAGE_TYPES = ("ADT", "ORM", "ORU")


def parse_hl7_message(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw.startswith("MSH"):
        return {"valid": False, "error": "missing MSH segment"}
    segments = [s for s in re.split(r"[\r\n]+", raw) if s.strip()]
    msh = segments[0].split("|")
    msg_type = ""
    for field in msh[6:10]:
        if field and any(field.startswith(t) for t in SUPPORTED_MESSAGE_TYPES):
            msg_type = field.split("^")[0]
            break
    if not msg_type and len(msh) > 8:
        parts = msh[8].split("^")
        msg_type = parts[0] if parts else msh[8]
    patient_ids: list[str] = []
    order_ids: list[str] = []
    observations: list[dict[str, str]] = []
    for seg in segments:
        fields = seg.split("|")
        kind = fields[0]
        if kind == "PID" and len(fields) > 3:
            patient_ids.append(fields[3].split("^")[0])
        if kind in {"OBR", "ORC"} and len(fields) > 3:
            order_ids.append(fields[3].split("^")[0])
        if kind == "OBX" and len(fields) > 5:
            observations.append({
                "test_code": fields[3].split("^")[0] if len(fields) > 3 else "",
                "value": fields[5],
                "unit": fields[6] if len(fields) > 6 else "",
            })
    supported = msg_type in SUPPORTED_MESSAGE_TYPES
    return {
        "valid": supported,
        "message_type": msg_type,
        "supported": supported,
        "patient_identifiers": patient_ids,
        "order_identifiers": order_ids,
        "observations": observations,
        "segment_count": len(segments),
        "message_hash": hashlib.sha256(raw.encode()).hexdigest(),
        "foundation_only": True,
    }
