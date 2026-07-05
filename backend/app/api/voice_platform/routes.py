"""Voice Platform API routes — Phase 7.6."""

from __future__ import annotations

from flask import Blueprint

from app.services.voice_platform_service import (
    dashboard_payload,
    speech_api,
    transcript_storage,
    clinical_note_generator,
    ai_summary,
    voice_session,
    voice_audit,
    voice_platform_readiness_report,
)

voice_platform_bp = Blueprint("voice_platform_api", __name__, url_prefix="/api/v1/voice-platform")

@voice_platform_bp.route("/dashboard", methods=["GET"])
def voice_platform_dashboard_api():
    return dashboard_payload()

@voice_platform_bp.route("/speech-api", methods=["GET"])
def voice_platform_speech_api_api():
    return speech_api()

@voice_platform_bp.route("/transcripts", methods=["GET"])
def voice_platform_transcript_storage_api():
    return transcript_storage()

@voice_platform_bp.route("/clinical-notes", methods=["GET"])
def voice_platform_clinical_note_generator_api():
    return clinical_note_generator()

@voice_platform_bp.route("/ai-summary", methods=["GET"])
def voice_platform_ai_summary_api():
    return ai_summary()

@voice_platform_bp.route("/sessions", methods=["GET"])
def voice_platform_voice_session_api():
    return voice_session()

@voice_platform_bp.route("/audit", methods=["GET"])
def voice_platform_voice_audit_api():
    return voice_audit()

@voice_platform_bp.route("/readiness", methods=["GET"])
def voice_platform_readiness_api():
    return voice_platform_readiness_report()
