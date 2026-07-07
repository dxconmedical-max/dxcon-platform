"""Launch UI Sprint 3 — safe demo data queries for product UI."""

from __future__ import annotations

from typing import Any

from app.services.reporting_service import _safe

from flask import session

FALLBACK_PATIENT_KEY = "P-DEMO-001"
FALLBACK_ORDER_KEY = "ORD-DEMO-001"
FALLBACK_REPORT_KEY = "RPT-DEMO-001"

_FALLBACK_COUNTS = {
    "patients": 86,
    "orders": 128,
    "tests": 42,
    "reports": 64,
    "samples": 42,
    "invoices": 55,
    "payments": 48,
    "revenue": 12450.0,
    "pending_reports": 8,
    "samples_in_transit": 12,
}

_FALLBACK_PATIENTS = [
    {
        "patient_code": "P-DEMO-001",
        "full_name": "Nguyen Van Demo",
        "phone": "0901234567",
        "gender": "Male",
        "email": "patient@demo.dxcon.test",
        "address": "District 1, Ho Chi Minh City",
    },
    {
        "patient_code": "P-DEMO-002",
        "full_name": "Tran Thi Demo",
        "phone": "0907654321",
        "gender": "Female",
        "email": "patient2@demo.dxcon.test",
        "address": "District 7, Ho Chi Minh City",
    },
]

_FALLBACK_ORDERS = [
    {
        "id": "demo-order-1",
        "order_code": "ORD-DEMO-001",
        "patient_id": "P-DEMO-001",
        "patient_name": "Nguyen Van Demo",
        "status": "PROCESSING",
        "total_amount": 45.0,
        "created_at": "Today",
    },
    {
        "id": "demo-order-2",
        "order_code": "ORD-DEMO-002",
        "patient_id": "P-DEMO-002",
        "patient_name": "Tran Thi Demo",
        "status": "COMPLETED",
        "total_amount": 120.0,
        "created_at": "Yesterday",
    },
]

_FALLBACK_REPORTS = [
    {
        "id": "RPT-DEMO-001",
        "test_name": "Complete Blood Count",
        "patient_name": "Nguyen Van Demo",
        "approval_status": "PENDING",
        "flag": "NORMAL",
        "result_value": "12.5",
        "unit": "g/dL",
    },
    {
        "id": "RPT-DEMO-002",
        "test_name": "Glucose",
        "patient_name": "Tran Thi Demo",
        "approval_status": "APPROVED",
        "flag": "HIGH",
        "result_value": "180",
        "unit": "mg/dL",
    },
]

_FALLBACK_SAMPLES = [
    {"sample_code": "S-DEMO-001", "status": "IN_TRANSIT", "patient_name": "Nguyen Van Demo"},
    {"sample_code": "S-DEMO-002", "status": "TESTING", "patient_name": "Tran Thi Demo"},
    {"sample_code": "S-DEMO-003", "status": "RECEIVED", "patient_name": "Le Van Demo"},
]

_FALLBACK_COLLECTIONS = [
    {
        "job_code": "COL-DEMO-001",
        "patient_name": "Nguyen Van Demo",
        "address": "District 1, HCMC",
        "status": "SCHEDULED",
        "eta": "30m",
    },
    {
        "job_code": "COL-DEMO-002",
        "patient_name": "Tran Thi Demo",
        "address": "District 7, HCMC",
        "status": "IN_PROGRESS",
        "eta": "1h",
    },
]


def get_session_patient_portal() -> dict[str, Any]:
    """Return patient-portal payload for the current session.

    This is used by Launch UI and the Sprint 009 patient portal UI as a safe
    fallback when real portal APIs are not used.
    """
    from app.business_engine import service as biz

    patient_code = session.get("patient_code") or session.get("patient_id") or FALLBACK_PATIENT_KEY
    payload = _safe(lambda: biz.get_patient_portal_data(patient_code)) or {}
    if payload:
        return payload
    # last resort fallback for demo sessions
    return {
        "patient": _FALLBACK_PATIENTS[0],
        "qr_payload": f"dxcon:patient:{_FALLBACK_PATIENTS[0]['patient_code']}",
        "orders": _FALLBACK_ORDERS,
        "invoices": [],
        "released_reports": [],
        "unreleased_report_count": 0,
    }


def _patient_name(patient_id: str) -> str:
    from app.models.patient import Patient

    patient = Patient.query.filter_by(patient_code=patient_id).first()
    return patient.full_name if patient else patient_id


def get_demo_counts() -> dict[str, Any]:
    from app.models.diagnostic_service import DiagnosticService
    from app.models.invoice import Invoice
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.payment import Payment
    from app.models.sample_tracking import SampleTracking
    from app.models.test_result import TestResult

    def fetch():
        payments = Payment.query.limit(500).all()
        revenue = round(sum(p.amount or 0 for p in payments), 2)
        pending_reports = TestResult.query.filter(
            TestResult.approval_status.in_(("PENDING", "DRAFT", "PENDING_REVIEW"))
        ).count()
        in_transit = SampleTracking.query.filter(
            SampleTracking.status.in_(("IN_TRANSIT", "COLLECTED", "CHECKED_IN"))
        ).count()
        return {
            "patients": Patient.query.count(),
            "orders": Order.query.count(),
            "tests": DiagnosticService.query.filter_by(is_active=True).count(),
            "reports": TestResult.query.count(),
            "samples": SampleTracking.query.count(),
            "invoices": Invoice.query.count(),
            "payments": Payment.query.count(),
            "revenue": revenue,
            "pending_reports": pending_reports,
            "samples_in_transit": in_transit,
        }

    return _safe(fetch, dict(_FALLBACK_COUNTS))


def get_recent_patients(limit: int = 10) -> list[dict[str, Any]]:
    from app.models.patient import Patient

    def fetch():
        rows = []
        for patient in Patient.query.order_by(Patient.created_at.desc()).limit(limit).all():
            rows.append(
                {
                    "patient_code": patient.patient_code,
                    "full_name": patient.full_name,
                    "phone": patient.phone or "—",
                    "gender": patient.gender or "—",
                    "email": patient.email or "—",
                    "address": patient.address or "—",
                }
            )
        return rows

    return _safe(fetch, list(_FALLBACK_PATIENTS))


def get_recent_orders(limit: int = 10) -> list[dict[str, Any]]:
    from app.models.biz_order import BizOrder
    from app.models.order import Order

    def fetch():
        rows = []
        for order in BizOrder.query.order_by(BizOrder.created_at.desc()).limit(limit).all():
            rows.append(
                {
                    "id": order.id,
                    "order_code": order.order_code,
                    "patient_id": order.patient_code,
                    "patient_name": order.patient_name,
                    "status": order.status or "draft",
                    "total_amount": order.total_amount or 0,
                    "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "—",
                    "source": "business",
                }
            )
        if len(rows) < limit:
            for order in Order.query.order_by(Order.created_at.desc()).limit(limit - len(rows)).all():
                rows.append(
                    {
                        "id": order.id,
                        "order_code": order.order_code,
                        "patient_id": order.patient_id,
                        "patient_name": _patient_name(order.patient_id),
                        "status": order.status or "PENDING",
                        "total_amount": order.total_amount or 0,
                        "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "—",
                        "source": "legacy",
                    }
                )
        return rows

    return _safe(fetch, list(_FALLBACK_ORDERS))


def get_recent_tests(limit: int = 10) -> list[dict[str, Any]]:
    from app.models.diagnostic_service import DiagnosticService
    from app.models.test_catalog import TestCatalog

    def fetch():
        rows = []
        for catalog in TestCatalog.query.limit(limit).all():
            rows.append(
                {
                    "id": catalog.id,
                    "service_code": catalog.code,
                    "code": catalog.code,
                    "name": catalog.name,
                    "sample_type": catalog.sample_type or "Blood",
                    "price": catalog.price or 0,
                    "turnaround_hours": 24,
                }
            )
        if rows:
            return rows
        for svc in DiagnosticService.query.filter_by(is_active=True).limit(limit).all():
            rows.append(
                {
                    "id": svc.id,
                    "service_code": svc.service_code,
                    "code": svc.service_code,
                    "name": svc.name,
                    "sample_type": svc.sample_type or "Blood",
                    "price": 0,
                    "turnaround_hours": svc.estimated_turnaround_hours or 24,
                }
            )
        return rows

    return _safe(
        fetch,
        [
            {"id": "demo-cbc", "service_code": "CBC", "code": "CBC", "name": "Complete Blood Count", "sample_type": "Blood", "price": 150000, "turnaround_hours": 4},
            {"id": "demo-glu", "service_code": "GLU", "code": "GLU", "name": "Glucose", "sample_type": "Blood", "price": 80000, "turnaround_hours": 2},
            {"id": "demo-lipid", "service_code": "LIPID", "code": "LIPID", "name": "Lipid Panel", "sample_type": "Blood", "price": 220000, "turnaround_hours": 6},
        ],
    )


def get_recent_reports(limit: int = 10) -> list[dict[str, Any]]:
    from app.business_engine import service as biz
    from app.models.order_item import OrderItem
    from app.models.order import Order
    from app.models.test_result import TestResult

    def fetch():
        biz_rows = biz.list_reports(limit)
        if biz_rows:
            return biz_rows
        rows = []
        for result in TestResult.query.order_by(TestResult.created_at.desc()).limit(limit).all():
            patient_name = "Demo Patient"
            try:
                item = OrderItem.query.filter_by(id=result.order_item_id).first()
                if item:
                    order = Order.query.filter_by(id=item.order_id).first()
                    if order:
                        patient_name = _patient_name(order.patient_id)
            except Exception:
                pass
            rows.append(
                {
                    "id": result.id,
                    "test_name": result.test_name or "Lab test",
                    "patient_name": patient_name,
                    "approval_status": result.approval_status or "PENDING",
                    "flag": result.flag or "NORMAL",
                    "result_value": result.result_value or "—",
                    "unit": result.unit or "",
                }
            )
        return rows

    return _safe(fetch, list(_FALLBACK_REPORTS))


def get_recent_collections(limit: int = 10) -> list[dict[str, Any]]:
    from app.business_engine import service as biz
    from app.models.sample_tracking import SampleTracking

    def fetch():
        biz_rows = biz.list_collections(limit)
        if biz_rows:
            return [
                {
                    "job_code": row.get("sample_code") or row.get("order_code"),
                    "patient_name": row.get("patient_name", "Patient"),
                    "address": row.get("pickup_address", "—"),
                    "status": row.get("status", "assigned").upper(),
                    "eta": "45m",
                }
                for row in biz_rows
            ]
        rows = []
        for sample in SampleTracking.query.order_by(SampleTracking.updated_at.desc()).limit(limit).all():
            rows.append(
                {
                    "job_code": sample.sample_code,
                    "patient_name": "Patient",
                    "address": f"Lat {sample.latitude or '—'}, Lng {sample.longitude or '—'}",
                    "status": sample.status or "SCHEDULED",
                    "eta": "45m",
                }
            )
        return rows

    return _safe(fetch, list(_FALLBACK_COLLECTIONS))


def get_finance_summary() -> dict[str, Any]:
    from app.business_engine import service as biz
    from app.models.invoice import Invoice
    from app.models.payment import Payment

    def fetch():
        biz_summary = biz.finance_summary()
        if biz_summary.get("invoice_total", 0) > 0:
            return {
                **biz_summary,
                "payment_methods": ["cash", "card", "bank_transfer"],
            }
        invoices = Invoice.query.limit(500).all()
        payments = Payment.query.limit(500).all()
        paid = sum(1 for inv in invoices if (inv.payment_status or "").upper() in {"PAID", "SETTLED"})
        pending = len(invoices) - paid
        revenue = round(sum(p.amount or 0 for p in payments), 2)
        return {
            "invoice_total": len(invoices),
            "paid_count": paid,
            "pending_count": max(pending, 0),
            "revenue": revenue,
            "payment_methods": ["Bank transfer", "Card", "Cash"],
        }

    return _safe(
        fetch,
        {
            "invoice_total": 55,
            "paid_count": 43,
            "pending_count": 12,
            "revenue": 12450.0,
            "payment_methods": ["Bank transfer", "Card", "Cash"],
        },
    )


def get_system_status() -> dict[str, Any]:
    from app.infrastructure.production_health import health_payload
    from flask import current_app

    def fetch():
        payload, _ = health_payload(current_app._get_current_object())
        return {
            "health": payload.get("status", "OK"),
            "database": payload.get("database", "OK"),
            "redis": payload.get("redis", "OK"),
            "environment": payload.get("app_env", "development"),
        }

    return _safe(
        fetch,
        {"health": "OK", "database": "OK", "redis": "DEGRADED", "environment": "development"},
    )


def get_top_test_categories(limit: int = 5) -> list[dict[str, Any]]:
    from app.models.diagnostic_category import DiagnosticCategory
    from app.models.diagnostic_service import DiagnosticService

    def fetch():
        rows = []
        for cat in DiagnosticCategory.query.limit(limit).all():
            count = DiagnosticService.query.filter_by(category_id=cat.id, is_active=True).count()
            rows.append({"category": cat.name, "tests": count})
        return rows

    return _safe(
        fetch,
        [
            {"category": "Hematology", "tests": 12},
            {"category": "Chemistry", "tests": 18},
            {"category": "Immunology", "tests": 8},
        ],
    )


def get_sample_patient_key() -> str:
    patients = get_recent_patients(1)
    return patients[0]["patient_code"] if patients else FALLBACK_PATIENT_KEY


def get_sample_order_key() -> str:
    orders = get_recent_orders(1)
    return orders[0]["order_code"] if orders else FALLBACK_ORDER_KEY


def get_sample_report_key() -> str:
    reports = get_recent_reports(1)
    return reports[0]["id"] if reports else FALLBACK_REPORT_KEY


def get_patient_detail(patient_key: str) -> dict[str, Any]:
    from app.business_engine import service as biz
    from app.models.patient import Patient

    def fetch():
        patient = Patient.query.filter_by(patient_code=patient_key).first()
        if not patient:
            return None
        return biz.patient_to_detail(patient)

    fallback = next((p for p in _FALLBACK_PATIENTS if p["patient_code"] == patient_key), _FALLBACK_PATIENTS[0])
    result = _safe(fetch, None)
    if result:
        return result
    return {
        **fallback,
        "orders": [o for o in _FALLBACK_ORDERS if o.get("patient_id") == fallback["patient_code"]],
    }


def get_order_detail(order_key: str) -> dict[str, Any]:
    from app.business_engine import service as biz
    from app.business_engine.service import BusinessEngineError
    from app.models.order import Order

    def fetch():
        try:
            return biz.order_to_detail(order_key)
        except BusinessEngineError:
            pass
        order = Order.query.filter(
            (Order.order_code == order_key) | (Order.id == order_key)
        ).first()
        if not order:
            return None
        return {
            "id": order.id,
            "order_code": order.order_code,
            "patient_id": order.patient_id,
            "patient_name": _patient_name(order.patient_id),
            "status": order.status or "PENDING",
            "total_amount": order.total_amount or 0,
            "created_at": order.created_at.strftime("%Y-%m-%d %H:%M") if order.created_at else "—",
            "timeline": [
                ("Ordered", order.created_at.strftime("%H:%M") if order.created_at else "—"),
                ("Sample collected", "—"),
                ("In lab", "—"),
                ("Report", "Pending"),
            ],
            "source": "legacy",
        }

    fallback = next((o for o in _FALLBACK_ORDERS if o["order_code"] == order_key), _FALLBACK_ORDERS[0])
    result = _safe(fetch, None)
    if result:
        return result
    return {
        **fallback,
        "timeline": [
            ("Ordered", "08:00"),
            ("Sample collected", "09:15"),
            ("In lab", "10:30"),
            ("Report", "Pending review"),
        ],
    }


def get_report_detail(report_key: str) -> dict[str, Any]:
    from app.business_engine import service as biz
    from app.business_engine.service import BusinessEngineError
    from app.models.test_result import TestResult

    def fetch():
        try:
            return biz.result_to_detail(report_key)
        except BusinessEngineError:
            pass
        result = TestResult.query.filter_by(id=report_key).first()
        if not result:
            return None
        return {
            "id": result.id,
            "test_name": result.test_name or "Lab test",
            "approval_status": result.approval_status or "PENDING",
            "flag": result.flag or "NORMAL",
            "result_value": result.result_value or "—",
            "unit": result.unit or "",
            "reference_range": result.reference_range or "—",
            "interpretation": result.interpretation or "Advisory AI summary pending clinician review.",
        }

    fallback = next((r for r in _FALLBACK_REPORTS if r["id"] == report_key), _FALLBACK_REPORTS[0])
    result = _safe(fetch, None)
    if result:
        return result
    return {
        **fallback,
        "reference_range": "70–100 mg/dL",
        "interpretation": "Elevated value — correlate with clinical presentation. Human approval required.",
    }


def get_recent_samples(limit: int = 10) -> list[dict[str, Any]]:
    from app.models.sample_tracking import SampleTracking

    def fetch():
        rows = []
        for sample in SampleTracking.query.order_by(SampleTracking.updated_at.desc()).limit(limit).all():
            rows.append(
                {
                    "sample_code": sample.sample_code,
                    "status": sample.status or "ORDERED",
                    "updated_at": sample.updated_at.strftime("%H:%M") if sample.updated_at else "—",
                }
            )
        return rows

    return _safe(fetch, [{"sample_code": s["sample_code"], "status": s["status"], "updated_at": "Today"} for s in _FALLBACK_SAMPLES])


def get_recent_invoices(limit: int = 10) -> list[dict[str, Any]]:
    from app.business_engine import service as biz
    from app.models.invoice import Invoice

    def fetch():
        biz_rows = biz.list_invoices(limit)
        if biz_rows:
            return biz_rows
        rows = []
        for invoice in Invoice.query.order_by(Invoice.created_at.desc()).limit(limit).all():
            rows.append(
                {
                    "invoice_no": invoice.invoice_no,
                    "amount": invoice.total_amount or 0,
                    "status": invoice.payment_status or "UNPAID",
                    "order_id": invoice.order_id,
                }
            )
        return rows

    return _safe(
        fetch,
        [
            {"invoice_no": "INV-DEMO-001", "amount": 45.0, "status": "PAID", "order_id": "demo-order-1"},
            {"invoice_no": "INV-DEMO-002", "amount": 120.0, "status": "UNPAID", "order_id": "demo-order-2"},
        ],
    )


def get_queue_summary() -> dict[str, int]:
    return _safe(
        lambda: {
            "waiting": 4,
            "checked_in": 2,
            "sampling": 1,
            "completed": 6,
        },
        {"waiting": 4, "checked_in": 2, "sampling": 1, "completed": 6},
    )
