"""Voice Platform web rendering helpers — Phase 7.6."""

from __future__ import annotations

import html
import json

from app.services import voice_platform_service as svc
from app.web.demo_pilot_lib import metric_cards, page_header, pilot_styles

NAV = (
    ("Overview", "/voice-platform"),
    ("Speech API", "/voice-platform/speech-api"),
    ("Transcript Storage", "/voice-platform/transcripts"),
    ("Clinical Note Generator", "/voice-platform/clinical-notes"),
    ("AI Summary", "/voice-platform/ai-summary"),
    ("Voice Session", "/voice-platform/sessions"),
    ("Voice Audit", "/voice-platform/audit")
)


def hub_styles() -> str:
    return pilot_styles() + """
    pre { background:#0f172a; color:#e2e8f0; padding:12px; border-radius:8px; overflow:auto; white-space:pre-wrap; font-size:13px; }
    .muted-note { color:#64748b; font-size:13px; margin-bottom:16px; }
    """


def render_hub_page(title: str, body_html: str) -> str:
    nav = "".join(f'<a href="{href}">{label}</a>' for label, href in NAV)
    return f"""
    <html>
    <head><title>{title}</title><meta name="viewport" content="width=device-width, initial-scale=1" /><style>{hub_styles()}</style></head>
    <body><div class="wrap"><div class="nav">{nav}</div><div class="muted-note">Voice Platform · Phase 7.6</div>{body_html}</div></body>
    </html>
    """


def build_json_section(title: str, data: dict) -> str:
    return f"""
    {page_header(title, data.get("report", ""))}
    <div class="card"><pre>{html.escape(json.dumps(data, indent=2, default=str))}</pre></div>
    """


def build_dashboard_body() -> str:
    data = svc.dashboard_payload()
    summary = data.get("summary", {})
    cards = metric_cards([(k.replace("_", " ").title(), v) for k, v in list(summary.items())[:6]])
    features = "".join(f"<li>{html.escape(item)}</li>" for item in data.get("features", []))
    return f"""
    {page_header("Voice Platform", "Phase 7.6 enterprise hub.")}
    {cards}
    <div class="card"><h3>Features</h3><ul>{features}</ul></div>
    """


def build_speech_api_body() -> str:
    return build_json_section('Speech API', svc.speech_api())

def build_transcript_storage_body() -> str:
    return build_json_section('Transcript Storage', svc.transcript_storage())

def build_clinical_note_generator_body() -> str:
    return build_json_section('Clinical Note Generator', svc.clinical_note_generator())

def build_ai_summary_body() -> str:
    return build_json_section('AI Summary', svc.ai_summary())

def build_voice_session_body() -> str:
    return build_json_section('Voice Session', svc.voice_session())

def build_voice_audit_body() -> str:
    return build_json_section('Voice Audit', svc.voice_audit())

