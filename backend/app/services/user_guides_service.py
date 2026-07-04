"""User guides and training business logic for Phase 5 Sprint 5.8."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.web.demo_pilot_lib import DEMO_PASSWORD, demo_accounts_by_role, seeded_summary, system_status

USER_GUIDES_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent

GUIDE_ASSETS = {
    "operations": REPO / "docs" / "OPERATIONS.md",
    "runbook": REPO / "docs" / "RUNBOOK.md",
    "recovery": REPO / "docs" / "RECOVERY.md",
    "pilot_checklist_script": ROOT / "scripts" / "go_live_checklist.txt",
}

FEATURES = (
    "Reception Guide",
    "Collector Guide",
    "Lab Guide",
    "Doctor Guide",
    "Admin Guide",
    "Video Link",
    "FAQ",
    "Checklist",
)

ROLE_GUIDES = {
    "reception": {
        "title": "Reception Guide",
        "summary": "Front desk registration, appointments, orders, and payment collection.",
        "routes": ["/reception", "/patients", "/orders/new", "/crm-pipeline"],
        "steps": [
            "Open the Reception Dashboard at /reception.",
            "Search or register the patient in /patients.",
            "Create a medical order at /orders/new and assign tests.",
            "Collect payment and confirm invoice status.",
            "Schedule home collection or direct the patient to sample pickup.",
        ],
        "demo_account_role": "reception",
    },
    "collector": {
        "title": "Collector Guide",
        "summary": "Field sample collection, cold-chain transport, and chain-of-custody scans.",
        "routes": ["/logistics", "/collector", "/logistics/dispatch", "/iot-box"],
        "steps": [
            "Review assigned pickups on the Logistics Dashboard at /logistics.",
            "Accept jobs in the Collector Portal at /collector.",
            "Scan sample boxes and confirm temperature on /iot-box.",
            "Start trip and update shipment status through dispatch.",
            "Hand off specimens to the receiving laboratory.",
        ],
        "demo_account_role": "collector",
    },
    "lab": {
        "title": "Lab Guide",
        "summary": "Specimen accession, processing, result upload, and validation.",
        "routes": ["/lab-operations", "/lab-worklist", "/results", "/result-files"],
        "steps": [
            "Open Lab Operations at /lab-operations for intake queue.",
            "Accession specimens and update worklist status.",
            "Upload analyzer or manual results via /result-files.",
            "Validate results and flag critical values.",
            "Release verified results to the doctor review queue.",
        ],
        "demo_account_role": "lab",
    },
    "doctor": {
        "title": "Doctor Guide",
        "summary": "Pending review queue, clinical sign-off, and patient report release.",
        "routes": ["/doctor-workbench", "/doctor/dashboard", "/doctor/results", "/workflow-demo"],
        "steps": [
            "Open Doctor Workbench at /doctor-workbench.",
            "Review pending and critical results.",
            "Approve or reject results with clinical comments.",
            "Release approved reports to the patient portal.",
            "Confirm patient notification delivery.",
        ],
        "demo_account_role": "doctor",
    },
    "admin": {
        "title": "Admin Guide",
        "summary": "Platform oversight, pilot dashboards, security, and release readiness.",
        "routes": [
            "/executive-v9",
            "/pilot-status",
            "/monitoring",
            "/security-compliance",
            "/demo-accounts",
        ],
        "steps": [
            "Monitor pilot operations at /pilot-status and /executive-v9.",
            "Verify health and alerts in /monitoring.",
            "Review security posture at /security-compliance.",
            "Use /demo-accounts for pilot login references.",
            "Run release verification before go-live promotion.",
        ],
        "demo_account_role": "admin",
    },
}

VIDEO_LINKS = (
    {
        "id": "workflow-demo",
        "title": "End-to-End Workflow Walkthrough",
        "type": "interactive",
        "url": "/workflow-demo",
        "description": "Interactive timeline from registration through notification.",
    },
    {
        "id": "pilot-overview",
        "title": "Pilot Platform Overview",
        "type": "dashboard",
        "url": "/executive-v9",
        "description": "Executive dashboard tour for pilot stakeholders.",
    },
    {
        "id": "operations-doc",
        "title": "Operations Runbook",
        "type": "documentation",
        "url": "/docs/OPERATIONS.md",
        "description": "Written operations reference in docs/OPERATIONS.md.",
    },
)

FAQ_ITEMS = (
    {
        "id": 1,
        "question": "What is the demo staff password?",
        "answer": f"Seeded demo staff accounts use password {DEMO_PASSWORD}. See /demo-accounts for emails.",
        "category": "Access",
    },
    {
        "id": 2,
        "question": "Where do I start a patient walk-in?",
        "answer": "Use /reception for the front desk queue, then /patients and /orders/new.",
        "category": "Reception",
    },
    {
        "id": 3,
        "question": "How does a collector accept a pickup?",
        "answer": "Open /logistics for the queue, then /collector to accept and start trips.",
        "category": "Collector",
    },
    {
        "id": 4,
        "question": "How are lab results released to patients?",
        "answer": "Lab validates at /lab-operations, doctor approves at /doctor-workbench, patient views at /patient-portal.",
        "category": "Clinical",
    },
    {
        "id": 5,
        "question": "Where is the pilot readiness checklist?",
        "answer": "Use /pilot-checklist for Phase 3A readiness and /user-guides/checklist for role training.",
        "category": "Pilot",
    },
    {
        "id": 6,
        "question": "Who can access admin dashboards?",
        "answer": "SUPER_ADMIN and ADMIN roles access executive, monitoring, and security hubs.",
        "category": "Admin",
    },
)


def ensure_user_guides() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def _role_guide(key: str) -> dict[str, Any]:
    spec = ROLE_GUIDES[key]
    accounts = demo_accounts_by_role().get(spec["demo_account_role"], [])[:3]
    return {
        "report": key,
        "read_only": True,
        "title": spec["title"],
        "summary": spec["summary"],
        "routes": spec["routes"],
        "steps": spec["steps"],
        "demo_accounts": accounts,
    }


def reception_guide() -> dict[str, Any]:
    ensure_user_guides()
    return _role_guide("reception")


def collector_guide() -> dict[str, Any]:
    ensure_user_guides()
    return _role_guide("collector")


def lab_guide() -> dict[str, Any]:
    ensure_user_guides()
    return _role_guide("lab")


def doctor_guide() -> dict[str, Any]:
    ensure_user_guides()
    return _role_guide("doctor")


def admin_guide() -> dict[str, Any]:
    ensure_user_guides()
    return _role_guide("admin")


def video_links() -> dict[str, Any]:
    ensure_user_guides()
    return {
        "report": "video_links",
        "read_only": True,
        "videos": list(VIDEO_LINKS),
        "count": len(VIDEO_LINKS),
        "primary": VIDEO_LINKS[0]["url"],
    }


def user_guides_faq() -> dict[str, Any]:
    ensure_user_guides()
    categories = sorted({item["category"] for item in FAQ_ITEMS})
    return {
        "report": "faq",
        "read_only": True,
        "items": list(FAQ_ITEMS),
        "count": len(FAQ_ITEMS),
        "categories": categories,
    }


def user_guides_checklist() -> dict[str, Any]:
    ensure_user_guides()
    status = system_status()
    summary = seeded_summary()
    seed_ok = summary["users"] > 0 and summary["patients"] > 0 and summary["orders"] > 0
    items = [
        {"item": "Review Reception Guide", "route": "/user-guides/reception", "required": True},
        {"item": "Review Collector Guide", "route": "/user-guides/collector", "required": True},
        {"item": "Review Lab Guide", "route": "/user-guides/lab", "required": True},
        {"item": "Review Doctor Guide", "route": "/user-guides/doctor", "required": True},
        {"item": "Review Admin Guide", "route": "/user-guides/admin", "required": True},
        {"item": "Watch workflow demo", "route": "/workflow-demo", "required": True},
        {"item": "Read FAQ", "route": "/user-guides/faq", "required": False},
        {"item": "Confirm demo seed data", "status": "OK" if seed_ok else "MISSING", "required": True},
        {"item": "System health probe", "status": status["status"], "required": True},
        {"item": "Legacy pilot checklist", "route": "/pilot-checklist", "required": False},
    ]
    return {
        "report": "checklist",
        "read_only": True,
        "items": items,
        "items_total": len(items),
        "seed_ok": seed_ok,
        "system_status": status,
        "legacy_route": "/pilot-checklist",
    }


def user_guides_dashboard() -> dict[str, Any]:
    ensure_user_guides()
    checklist = user_guides_checklist()
    return {
        "report": "user_guides_dashboard",
        "read_only": True,
        "status": "OK" if checklist["seed_ok"] else "WARN",
        "role_guides": len(ROLE_GUIDES),
        "faq_count": len(FAQ_ITEMS),
        "video_count": len(VIDEO_LINKS),
        "checklist_items": checklist["items_total"],
    }


def user_guides_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.8",
        "sprint": "User Guides",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "reception": reception_guide(),
            "collector": collector_guide(),
            "lab": lab_guide(),
            "doctor": doctor_guide(),
            "admin": admin_guide(),
            "video": video_links(),
            "faq": user_guides_faq(),
            "checklist": user_guides_checklist(),
        },
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_user_guides()
    dash = user_guides_dashboard()
    return {
        "platform": "User Guides",
        "phase": "5.8",
        "sprint": "User Guides",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "role_guides": dash["role_guides"],
            "faq_count": dash["faq_count"],
            "video_count": dash["video_count"],
            "checklist_items": dash["checklist_items"],
        },
        "features": list(FEATURES),
    }
