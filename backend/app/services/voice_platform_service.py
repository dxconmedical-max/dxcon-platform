"""Voice Platform business logic for Phase 7.6."""

from __future__ import annotations

from datetime import datetime
from typing import Any

VOICE_PLATFORM_ROLES = ("SUPER_ADMIN", "ADMIN", "DOCTOR")

FEATURES = (
    "Speech API",
    "Transcript Storage",
    "Clinical Note Generator",
    "AI Summary",
    "Voice Session",
    "Voice Audit",
)

_VOICE_SESSIONS: list[dict] = []
_VOICE_TRANSCRIPTS: list[dict] = []


def ensure_voice_platform() -> dict[str, Any]:
    return {"ready": True, "scaffold": True}


def speech_api() -> dict[str, Any]:
    return {
        "report": "speech_api",
        "status": "SCAFFOLD",
        "supported": ["audio/wav", "audio/webm"],
        "endpoint": "/api/v1/voice-platform/speech",
    }


def transcript_storage() -> dict[str, Any]:
    return {"report": "transcript_storage", "count": len(_VOICE_TRANSCRIPTS), "storage": "in_memory_scaffold"}


def clinical_note_generator() -> dict[str, Any]:
    return {
        "report": "clinical_note_generator",
        "advisory_only": True,
        "human_review_required": True,
        "status": "SCAFFOLD",
    }


def ai_summary() -> dict[str, Any]:
    return {"report": "ai_summary", "advisory_only": True, "status": "SCAFFOLD"}


def voice_session() -> dict[str, Any]:
    return {"report": "voice_session", "active_sessions": len(_VOICE_SESSIONS), "status": "SCAFFOLD"}


def voice_audit() -> dict[str, Any]:
    return {"report": "voice_audit", "entries": len(_VOICE_TRANSCRIPTS), "status": "SCAFFOLD"}


def dashboard_payload() -> dict[str, Any]:
    return {
        "platform": "Voice Platform",
        "phase": "7.6",
        "sprint": "Voice Platform",
        "status": "SCAFFOLD",
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {"features_scaffolded": len(FEATURES), "transcripts": len(_VOICE_TRANSCRIPTS)},
        "features": list(FEATURES),
    }


def voice_platform_readiness_report() -> dict[str, Any]:
    d = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "7.6",
        "platform": d["platform"],
        "status": d["status"],
        "summary": d["summary"],
        "features": list(FEATURES),
        "sections": {
            "speech_api": speech_api(),
            "transcript_storage": transcript_storage(),
            "clinical_note_generator": clinical_note_generator(),
            "ai_summary": ai_summary(),
            "voice_session": voice_session(),
            "voice_audit": voice_audit(),
        },
        "guide": "docs/VOICE_PLATFORM_GUIDE.md",
    }
