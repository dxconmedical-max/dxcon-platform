"""Launch UI Sprint 4 — safe demo actions (no destructive DB writes)."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode

from flask import request

from app.web.launch_ui_lib import breadcrumbs, render_page, status_badge

_SAFE_KEY = re.compile(r"^[a-zA-Z0-9._-]{1,80}$")

ACTION_SLUGS: tuple[str, ...] = (
    "check-in-patient",
    "create-demo-order",
    "mark-paid",
    "assign-collector",
    "collect-sample",
    "receive-sample",
    "start-testing",
    "complete-qc",
    "doctor-approve",
    "release-report",
    "send-notification",
)

ACTION_META: dict[str, dict[str, str]] = {
    "check-in-patient": {
        "label": "Check in patient",
        "entity_type": "patient",
        "next_label": "View reception queue",
        "next_href": "/app/reception/queue",
    },
    "create-demo-order": {
        "label": "Create demo order",
        "entity_type": "order",
        "next_label": "Open orders",
        "next_href": "/app/orders",
    },
    "mark-paid": {
        "label": "Mark payment received",
        "entity_type": "invoice",
        "next_label": "Open finance",
        "next_href": "/app/finance",
    },
    "assign-collector": {
        "label": "Assign collector",
        "entity_type": "collection",
        "next_label": "Pickup queue",
        "next_href": "/app/collections",
    },
    "collect-sample": {
        "label": "Collect sample",
        "entity_type": "sample",
        "next_label": "Chain of custody",
        "next_href": "/app/samples/chain-of-custody",
    },
    "receive-sample": {
        "label": "Receive sample at lab",
        "entity_type": "sample",
        "next_label": "Sample accession",
        "next_href": "/app/samples/accession",
    },
    "start-testing": {
        "label": "Start testing",
        "entity_type": "sample",
        "next_label": "Lab testing",
        "next_href": "/app/lab/testing",
    },
    "complete-qc": {
        "label": "Complete QC",
        "entity_type": "qc_run",
        "next_label": "Lab QC",
        "next_href": "/app/lab/qc",
    },
    "doctor-approve": {
        "label": "Doctor approve report",
        "entity_type": "report",
        "next_label": "Reports queue",
        "next_href": "/app/reports",
    },
    "release-report": {
        "label": "Release report to patient",
        "entity_type": "report",
        "next_label": "Patient reports",
        "next_href": "/app/patient/reports",
    },
    "send-notification": {
        "label": "Send notification",
        "entity_type": "notification",
        "next_label": "Patient notifications",
        "next_href": "/app/patient/notifications",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def sanitize_entity_key(raw: str | None, fallback: str = "demo") -> str:
    value = (raw or fallback).strip()
    if _SAFE_KEY.match(value):
        return value
    return fallback


def demo_action_result(action_name: str, entity_type: str, entity_key: str) -> dict[str, Any]:
    meta = None
    slug = ""
    for s, m in ACTION_META.items():
        if m["label"] == action_name:
            meta = m
            slug = s
            break
    return {
        "action_name": action_name,
        "entity_type": entity_type or (meta or {}).get("entity_type", "entity"),
        "entity_key": entity_key or "demo",
        "success": True,
        "message": f"{action_name} simulated successfully. No production data was modified.",
        "timestamp": _utc_now(),
        "next_action": (meta or {}).get("next_label", "Continue"),
        "next_href": (meta or {}).get("next_href", "/app/executive"),
        "slug": slug,
    }


def demo_action_result_for_slug(slug: str, entity_type: str, entity_key: str) -> dict[str, Any]:
    meta = ACTION_META.get(slug, {})
    label = meta.get("label", slug.replace("-", " ").title())
    result = demo_action_result(label, entity_type or meta.get("entity_type", "entity"), entity_key)
    result["slug"] = slug
    return result


def action_href(slug: str, entity_key: str = "demo", entity_type: str = "", return_href: str = "") -> str:
    meta = ACTION_META.get(slug, {})
    params = {
        "entity_key": sanitize_entity_key(entity_key),
        "entity_type": entity_type or meta.get("entity_type", "entity"),
    }
    if return_href:
        params["return"] = return_href
    return f"/app/actions/{slug}?{urlencode(params)}"


def action_button(label: str, slug: str, entity_key: str = "demo", entity_type: str = "", return_href: str = "", *, primary: bool = False) -> str:
    css = "launch-btn launch-btn-sm" if primary else "launch-btn-outline launch-btn-sm"
    href = html.escape(action_href(slug, entity_key, entity_type, return_href))
    return f'<a class="{css}" href="{href}">{html.escape(label)}</a>'


def demo_success_banner(result: dict[str, Any]) -> str:
    return (
        '<div class="launch-card launch-toast launch-toast-success">'
        f'<div class="launch-toast-title">{status_badge("SUCCESS")} '
        f'<span>{html.escape(result["action_name"])}</span></div>'
        f'<p>{html.escape(result["message"])}</p>'
        f'<p class="launch-hint"><strong>Entity:</strong> {html.escape(result["entity_type"])} · '
        f'<code>{html.escape(result["entity_key"])}</code> · '
        f'<strong>Time:</strong> {html.escape(result["timestamp"])}</p>'
        f'<p class="launch-hint"><strong>Next step:</strong> {html.escape(result["next_action"])}</p>'
        f'<div class="launch-footer-actions">'
        f'<a class="launch-btn" href="{html.escape(result["next_href"])}">{html.escape(result["next_action"])}</a>'
        "</div></div>"
    )


def render_action_success_body(result: dict[str, Any], return_href: str = "") -> str:
    back = ""
    if return_href:
        back = f'<p class="launch-back"><a class="launch-btn-outline" href="{html.escape(return_href)}">← Back</a></p>'
    return (
        breadcrumbs([("Actions", "/app/executive"), ("Success", "#")])
        + back
        + demo_success_banner(result)
    )


def handle_demo_action(slug: str) -> str:
    if slug not in ACTION_SLUGS:
        result = {
            "action_name": "Unknown action",
            "entity_type": "entity",
            "entity_key": "demo",
            "success": False,
            "message": "Unknown demo action requested.",
            "timestamp": _utc_now(),
            "next_action": "Return to dashboard",
            "next_href": "/app/executive",
        }
        return render_action_success_body(result)

    payload = request.values
    entity_key = sanitize_entity_key(payload.get("entity_key"))
    entity_type = sanitize_entity_key(payload.get("entity_type"), "entity")
    return_href = payload.get("return") or ""
    if return_href and not return_href.startswith("/app/"):
        return_href = "/app/executive"

    result = demo_action_result_for_slug(slug, entity_type, entity_key)
    if return_href:
        result["next_href"] = return_href
        result["next_action"] = "Return to previous page"
    return render_action_success_body(result, return_href)


def workflow_stage_cards(stages: list[tuple[str, str, str]]) -> str:
    """Stage label, status, timestamp."""
    cards = []
    for label, status, when in stages:
        cards.append(
            f'<div class="launch-card launch-workflow-card">'
            f"<label>{html.escape(label)}</label>"
            f"{status_badge(status)}"
            f'<span class="launch-workflow-time">{html.escape(when)}</span></div>'
        )
    return f'<div class="launch-grid launch-workflow-grid">{"".join(cards)}</div>'


def action_button_row(buttons: list[str]) -> str:
    return f'<div class="launch-card"><h3>Workflow actions</h3><div class="launch-footer-actions">{"".join(buttons)}</div></div>'
