"""Pilot toolkit business logic for Phase 5 Sprint 5.13."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.developer_portal_service import api_documentation_links, postman_collection_link
from app.services.reporting_service import ExecutiveDashboardService, KPIService, ReportingService, _safe
from app.web.demo_pilot_lib import DEMO_ORDER_PREFIX, DEMO_PASSWORD, demo_accounts_by_role, seeded_summary, system_status
from app.web.pilot_dashboard_data import WORKFLOW_TIMELINE

PILOT_TOOLKIT_ROLES = ("SUPER_ADMIN", "ADMIN")

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parent
GENERATED = ROOT / "generated_release"
POSTMAN_PATH = ROOT / "generated_api" / "postman_collection.json"
OPENAPI_JSON = ROOT / "generated_api" / "openapi.json"
OPENAPI_YAML = ROOT / "generated_api" / "openapi.yaml"

FEATURES = (
    "Demo Accounts",
    "Demo Data",
    "Postman",
    "Swagger",
    "Workflow",
    "PDF",
    "QR",
    "Reports",
)


def ensure_pilot_toolkit() -> dict[str, Any]:
    return {"ready": True, "read_only": True}


def demo_accounts() -> dict[str, Any]:
    ensure_pilot_toolkit()
    accounts = demo_accounts_by_role()
    totals = {role: len(rows) for role, rows in accounts.items()}
    return {
        "report": "demo_accounts",
        "read_only": True,
        "demo_password": DEMO_PASSWORD,
        "accounts_by_role": accounts,
        "totals_by_role": totals,
        "accounts_total": sum(totals.values()),
        "web_route": "/demo-accounts",
        "login_route": "/login",
    }


def demo_data() -> dict[str, Any]:
    ensure_pilot_toolkit()
    summary = seeded_summary()
    status = system_status()
    seed_report = None
    seed_path = GENERATED / "DEMO_SEED_REPORT.json"
    if seed_path.exists():
        try:
            seed_report = json.loads(seed_path.read_text(encoding="utf-8"))
        except Exception:
            seed_report = None
    return {
        "report": "demo_data",
        "read_only": True,
        "seeded_summary": summary,
        "system_status": status,
        "seed_report_available": seed_path.exists(),
        "seed_report_summary": (seed_report or {}).get("summary"),
        "seed_api": "POST /api/v1/seeds/demo-operations",
        "prefixes": {
            "orders": DEMO_ORDER_PREFIX,
            "patients": "DEMO-PAT-",
            "tests": "DEMO-TST-",
            "users": "demo-",
        },
        "docs": "backend/docs/DEMO_SEED_DATA.md",
    }


def postman_toolkit() -> dict[str, Any]:
    ensure_pilot_toolkit()
    link = postman_collection_link()
    item_count = 0
    if POSTMAN_PATH.exists():
        try:
            payload = json.loads(POSTMAN_PATH.read_text(encoding="utf-8"))
            item_count = len(payload.get("item", []))
        except Exception:
            item_count = 0
    return {
        "report": "postman",
        "read_only": True,
        "collection_url": link.get("collection_url"),
        "collection_path": str(POSTMAN_PATH.relative_to(REPO)) if POSTMAN_PATH.exists() else None,
        "collection_available": POSTMAN_PATH.exists(),
        "collection_items": item_count,
        "openapi_import": link.get("openapi_import"),
        "instructions": link.get("instructions", []),
        "legacy_hub": "/developer-portal/postman",
    }


def swagger_toolkit() -> dict[str, Any]:
    ensure_pilot_toolkit()
    docs = api_documentation_links()
    return {
        "report": "swagger",
        "read_only": True,
        "openapi_json": docs.get("openapi_json"),
        "openapi_yaml": docs.get("openapi_yaml"),
        "swagger_ui": docs.get("swagger_ui"),
        "redoc": docs.get("redoc"),
        "docs_index": docs.get("docs_index"),
        "files": {
            "openapi_json": OPENAPI_JSON.exists(),
            "openapi_yaml": OPENAPI_YAML.exists(),
        },
        "legacy_routes": ["/api-docs/swagger", "/api-docs/redoc", "/developer-portal"],
    }


def workflow_toolkit() -> dict[str, Any]:
    ensure_pilot_toolkit()
    steps = [
        {
            "step": index + 1,
            "label": label,
            "route": href,
            "detail": detail,
        }
        for index, (label, href, detail) in enumerate(WORKFLOW_TIMELINE)
    ]
    return {
        "report": "workflow",
        "read_only": True,
        "steps_total": len(steps),
        "steps": steps,
        "web_route": "/workflow-demo",
        "timeline": " → ".join(label for label, _, _ in WORKFLOW_TIMELINE),
    }


def pdf_toolkit(limit: int = 10) -> dict[str, Any]:
    ensure_pilot_toolkit()
    from app.models.order import Order
    from app.models.order_item import OrderItem
    from app.models.test_result import TestResult

    orders = _safe(
        lambda: Order.query.filter(Order.order_code.like(f"{DEMO_ORDER_PREFIX}%"))
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all(),
        [],
    )
    samples = []
    for order in orders:
        item_ids = [
            item.id
            for item in _safe(lambda oid=order.id: OrderItem.query.filter_by(order_id=oid).all(), [])
        ]
        has_results = bool(
            item_ids
            and _safe(
                lambda ids=item_ids: TestResult.query.filter(TestResult.order_item_id.in_(ids)).count(),
                0,
            )
        )
        samples.append(
            {
                "order_id": order.id,
                "order_code": order.order_code,
                "pdf_route": f"/results/report/{order.id}/pdf",
                "has_results": has_results,
            }
        )

    return {
        "report": "pdf",
        "read_only": True,
        "pdf_route_pattern": "/results/report/<order_id>/pdf",
        "demo_orders": samples,
        "demo_orders_total": len(samples),
        "orders_with_results": sum(1 for row in samples if row["has_results"]),
        "legacy_hub": "/reports",
    }


def qr_toolkit(limit: int = 10) -> dict[str, Any]:
    ensure_pilot_toolkit()
    from app.models.transport_box import TransportBox

    boxes = _safe(
        lambda: TransportBox.query.order_by(TransportBox.created_at.desc()).limit(limit).all(),
        [],
    )
    rows = [
        {
            "box_id": box.id,
            "box_code": box.box_code,
            "qr_route": f"/boxes/{box.id}/qr",
            "qr_route_by_code": f"/boxes/{box.box_code}/qr",
            "status": getattr(box, "status", None),
        }
        for box in boxes
    ]
    return {
        "report": "qr",
        "read_only": True,
        "qr_route_pattern": "/boxes/<box_id>/qr",
        "transport_boxes": rows,
        "boxes_total": len(rows),
        "related_routes": ["/transport-boxes", "/logistics-v2", "/iot-box"],
    }


def reports_toolkit() -> dict[str, Any]:
    ensure_pilot_toolkit()
    kpi = _safe(KPIService.get_kpi_summary, {})
    revenue = _safe(ReportingService.revenue_summary, {})
    executive = _safe(ExecutiveDashboardService.get_dashboard, {})
    return {
        "report": "reports",
        "read_only": True,
        "kpi_summary": kpi,
        "revenue_summary": revenue,
        "executive_dashboard": executive,
        "web_routes": [
            "/reports",
            "/reports/executive",
            "/reports/operations",
        ],
        "api_routes": [
            "/api/v1/reports/kpi",
            "/api/v1/reports/revenue",
            "/api/v1/reports/operations",
            "/api/v1/reports/partners",
            "/api/v1/reports/collectors",
        ],
    }


def pilot_toolkit_dashboard() -> dict[str, Any]:
    ensure_pilot_toolkit()
    accounts = demo_accounts()
    data = demo_data()
    postman = postman_toolkit()
    swagger = swagger_toolkit()
    workflow = workflow_toolkit()
    pdf = pdf_toolkit(limit=5)
    qr = qr_toolkit(limit=5)
    reports = reports_toolkit()
    status = "OK" if data["seeded_summary"]["orders"] > 0 else "WARN"
    return {
        "report": "pilot_toolkit_dashboard",
        "read_only": True,
        "status": status,
        "demo_accounts_total": accounts["accounts_total"],
        "demo_orders": data["seeded_summary"]["orders"],
        "postman_available": postman["collection_available"],
        "swagger_available": swagger["files"]["openapi_json"],
        "workflow_steps": workflow["steps_total"],
        "pdf_samples": pdf["demo_orders_total"],
        "qr_boxes": qr["boxes_total"],
        "reports_kpi_orders": reports["kpi_summary"].get("orders_total", 0),
    }


def pilot_toolkit_readiness_report() -> dict[str, Any]:
    dashboard = dashboard_payload()
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "phase": "5.13",
        "sprint": "Pilot Toolkit",
        "platform": dashboard["platform"],
        "status": dashboard["status"],
        "summary": dashboard["summary"],
        "features": list(FEATURES),
        "sections": {
            "demo_accounts": demo_accounts(),
            "demo_data": demo_data(),
            "postman": postman_toolkit(),
            "swagger": swagger_toolkit(),
            "workflow": workflow_toolkit(),
            "pdf": pdf_toolkit(),
            "qr": qr_toolkit(),
            "reports": reports_toolkit(),
        },
        "legacy_routes": [
            "/demo-accounts",
            "/workflow-demo",
            "/developer-portal",
            "/api-docs/swagger",
            "/reports",
        ],
    }


def dashboard_payload() -> dict[str, Any]:
    ensure_pilot_toolkit()
    dash = pilot_toolkit_dashboard()
    accounts = demo_accounts()
    data = demo_data()
    return {
        "platform": "Pilot Toolkit",
        "phase": "5.13",
        "sprint": "Pilot Toolkit",
        "status": dash["status"],
        "read_only": True,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": {
            "demo_accounts_total": accounts["accounts_total"],
            "demo_orders": data["seeded_summary"]["orders"],
            "demo_patients": data["seeded_summary"]["patients"],
            "postman_available": dash["postman_available"],
            "swagger_available": dash["swagger_available"],
            "workflow_steps": dash["workflow_steps"],
            "pdf_samples": dash["pdf_samples"],
            "qr_boxes": dash["qr_boxes"],
        },
        "features": list(FEATURES),
    }
