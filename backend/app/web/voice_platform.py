"""Voice Platform web routes — Phase 7.6."""

from __future__ import annotations

from flask import Blueprint

from app.services.voice_platform_service import VOICE_PLATFORM_ROLES
from app.utils.auth import role_required
from app.web.voice_platform_lib import (
    build_dashboard_body,
    build_speech_api_body,
    build_transcript_storage_body,
    build_clinical_note_generator_body,
    build_ai_summary_body,
    build_voice_session_body,
    build_voice_audit_body,
    render_hub_page,
)

voice_platform_web_bp = Blueprint("voice_platform_web", __name__)

@voice_platform_web_bp.route("/voice-platform")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_dashboard():
    return render_hub_page("Voice Platform", build_dashboard_body())
@voice_platform_web_bp.route("/voice-platform/speech-api")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_speech_api():
    return render_hub_page("Speech API", build_speech_api_body())
@voice_platform_web_bp.route("/voice-platform/transcripts")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_transcript_storage():
    return render_hub_page("Transcript Storage", build_transcript_storage_body())
@voice_platform_web_bp.route("/voice-platform/clinical-notes")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_clinical_note_generator():
    return render_hub_page("Clinical Note Generator", build_clinical_note_generator_body())
@voice_platform_web_bp.route("/voice-platform/ai-summary")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_ai_summary():
    return render_hub_page("AI Summary", build_ai_summary_body())
@voice_platform_web_bp.route("/voice-platform/sessions")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_voice_session():
    return render_hub_page("Voice Session", build_voice_session_body())
@voice_platform_web_bp.route("/voice-platform/audit")
@role_required(*VOICE_PLATFORM_ROLES)
def voice_platform_voice_audit():
    return render_hub_page("Voice Audit", build_voice_audit_body())

