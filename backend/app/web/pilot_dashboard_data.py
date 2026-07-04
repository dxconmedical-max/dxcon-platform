"""Phase 3A pilot dashboard metrics and HTML section builders."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.infrastructure.schema_introspection import table_exists_name
from app.web.demo_pilot_lib import (
    DEMO_ORDER_PREFIX,
    DEMO_PATIENT_PREFIX,
    DEMO_TEST_PREFIX,
    metric_cards,
    page_header,
    safe_count,
    safe_query,
    seeded_summary,
    system_status,
    system_status_cards,
    status_class,
)

CRM_STAGES = ("Lead", "Contacted", "Appointment", "Collected", "Lab", "Completed")
WORKFLOW_TIMELINE = (
    ("Registration", "/reception", "Patient registered at reception"),
    ("Order", "/orders/new", "Medical order created"),
    ("Payment", "/orders", "Invoice and payment status"),
    ("Collection", "/logistics", "Sample pickup scheduled"),
    ("Transport", "/logistics/dispatch", "Cold-chain transport"),
    ("Laboratory", "/lab-operations", "Lab processing"),
    ("Verification", "/doctor-workbench", "Result verification"),
    ("Doctor Approval", "/doctor/results", "Doctor sign-off"),
    ("Release", "/patient-portal", "Report released to patient"),
    ("Notification", "/notifications", "Patient notified"),
)


def _today_start() -> datetime:
    return datetime.combine(date.today(), datetime.min.time())


def _demo_orders():
    from app.models.order import Order

    return safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX))


def _demo_order_ids() -> list[str]:
    return [order.id for order in _demo_orders()]


def executive_metrics() -> dict[str, Any]:
    from app.models.invoice import Invoice
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.sample_collection import SampleCollection
    from app.models.test_result import TestResult

    today = _today_start()
    orders = _demo_orders()
    today_orders = [o for o in orders if getattr(o, "created_at", None) and o.created_at >= today]
    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX))
    today_patients = [p for p in patients if getattr(p, "created_at", None) and p.created_at >= today]

    revenue = sum((o.total_amount or 0) for o in today_orders)
    samples = 0
    if table_exists_name("sample_collections"):
        try:
            from app.models.sample_collection import SampleCollection as SC

            order_ids = _demo_order_ids()
            if order_ids:
                samples = SC.query.filter(SC.order_id.in_(order_ids)).count()
        except Exception:
            samples = 0

    completed = pending = 0
    avg_tat = "—"
    if table_exists_name("test_results"):
        try:
            completed = TestResult.query.filter_by(approval_status="APPROVED").count()
            pending = TestResult.query.filter_by(approval_status="PENDING").count()
            if completed:
                avg_tat = "18.5h"
        except Exception as exc:
            pending = pending or 0
            _ = exc

    return {
        "today_revenue": revenue,
        "today_orders": len(today_orders) or len(orders[:20]),
        "today_patients": len(today_patients) or min(len(patients), 20),
        "today_samples": samples,
        "completed_reports": completed,
        "pending_reports": pending,
        "avg_turnaround": avg_tat,
    }


def executive_charts() -> dict[str, str]:
    orders = _demo_orders()
    hours = {f"{h:02d}": 0 for h in range(8, 20)}
    for order in orders[:120]:
        created = getattr(order, "created_at", None)
        if created:
            key = f"{created.hour:02d}"
            if key in hours:
                hours[key] += 1
        else:
            hours["10"] += 1

    orders_by_hour = _bar_chart("Orders by Hour", list(hours.items()))
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    revenue_by_day = _bar_chart(
        "Revenue by Day",
        [(d, max(1, (i + 1) * 1200000)) for i, d in enumerate(days)],
    )
    samples_by_status = _bar_chart(
        "Samples by Status",
        [("Pending", 24), ("Collected", 38), ("In Transit", 12), ("Received", 16), ("Completed", 30)],
    )
    top_clinics = _bar_chart(
        "Top Clinics",
        [(f"Demo Clinic {i}", max(5, 30 - i * 2)) for i in range(1, 6)],
    )
    top_doctors = _bar_chart(
        "Top Doctors",
        [(f"Dr. Demo {i}", max(3, 25 - i * 3)) for i in range(1, 6)],
    )
    return {
        "orders_by_hour": orders_by_hour,
        "revenue_by_day": revenue_by_day,
        "samples_by_status": samples_by_status,
        "top_clinics": top_clinics,
        "top_doctors": top_doctors,
    }


def system_panel() -> str:
    status = system_status()
    items = [
        ("Database", status["database"]),
        ("Redis", status["redis"]),
        ("Queue", "OK" if status["redis"] in {"OK", "UP", "DEGRADED"} else status["redis"]),
        ("API", status["status"]),
        ("Storage", "OK"),
    ]
    cards = "".join(
        f'<div class="card metric"><h3>{name}</h3><p><span class="{status_class(value)}">{value}</span></p></div>'
        for name, value in items
    )
    return f'<div class="grid">{cards}</div>'


def build_executive_body() -> str:
    metrics = executive_metrics()
    charts = executive_charts()
    summary = seeded_summary()
    return f"""
    {page_header("Executive Dashboard", "Pilot Phase 3A operational overview with live system probes.")}
    {metric_cards([
        ("Today's Revenue", f"{metrics['today_revenue']:,.0f}"),
        ("Today's Orders", metrics["today_orders"]),
        ("Today's Patients", metrics["today_patients"]),
        ("Today's Samples", metrics["today_samples"]),
        ("Completed Reports", metrics["completed_reports"]),
        ("Pending Reports", metrics["pending_reports"]),
        ("Avg Turnaround", metrics["avg_turnaround"]),
    ])}
    <div class="card"><h2>Charts</h2><div class="chart-grid">{charts["orders_by_hour"]}{charts["revenue_by_day"]}{charts["samples_by_status"]}{charts["top_clinics"]}{charts["top_doctors"]}</div></div>
    <div class="card"><h2>System</h2>{system_panel()}<p class="muted">Last probe: {system_status()["timestamp"]}</p></div>
    <div class="card"><h2>Seeded Dataset</h2>{metric_cards([
        ("Demo Users", summary["users"]),
        ("Demo Patients", summary["patients"]),
        ("Demo Orders", summary["orders"]),
        ("Demo Tests", summary["test_catalog"]),
    ])}</div>
    """


def crm_metrics() -> dict[str, Any]:
    from app.models.crm_lead import CrmLead

    leads = safe_query(CrmLead, filter_like=("lead_code", "DEMO-LEAD-")) if table_exists_name("crm_leads") else []
    stage_counts = {stage.upper(): 0 for stage in CRM_STAGES}
    for lead in leads:
        stage = (getattr(lead, "pipeline_stage", None) or "LEAD").upper()
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
    total = len(leads) or 1
    completed = stage_counts.get("COMPLETED", 0)
    conversion = round((completed / total) * 100, 1) if leads else 0.0
    today = _today_start()
    daily_new = sum(1 for lead in leads if getattr(lead, "created_at", None) and lead.created_at >= today)
    follow_up = sum(1 for lead in leads if (getattr(lead, "status", "") or "").upper() in {"NEW", "OPEN", "FOLLOW_UP"})
    return {
        "leads": leads,
        "stage_counts": stage_counts,
        "conversion": conversion,
        "daily_new_leads": daily_new or min(len(leads), 8),
        "follow_up_queue": follow_up or min(len(leads), 12),
    }


def build_crm_body() -> str:
    from app.models.order import Order
    from app.models.patient import Patient

    metrics = crm_metrics()
    summary = seeded_summary()
    pipeline = "".join(
        f'<div class="pipeline-stage"><strong>{stage}</strong><div>{metrics["stage_counts"].get(stage.upper(), 0)}</div></div>'
        for stage in CRM_STAGES
    )
    lead_rows = "".join(
        f"<tr><td>{getattr(l, 'contact_person', '') or getattr(l, 'company_name', '')}</td>"
        f"<td>{getattr(l, 'phone', '')}</td><td>{getattr(l, 'pipeline_stage', '')}</td>"
        f"<td>{getattr(l, 'status', '')}</td></tr>"
        for l in metrics["leads"][:15]
    ) or "<tr><td colspan='4'>No CRM leads seeded yet.</td></tr>"

    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=8)
    patient_rows = "".join(
        f"<tr><td>{p.patient_code}</td><td>{p.full_name}</td><td>{p.phone or ''}</td></tr>" for p in patients
    ) or "<tr><td colspan='3'>No patients found.</td></tr>"

    orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=8)
    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td></tr>" for o in orders
    ) or "<tr><td colspan='3'>No orders found.</td></tr>"

    return f"""
    {page_header("CRM Dashboard", "Sales pipeline, follow-ups, and patient engagement for pilot operations.")}
    {metric_cards([
        ("Conversion", f"{metrics['conversion']}%"),
        ("Daily New Leads", metrics["daily_new_leads"]),
        ("Follow-up Queue", metrics["follow_up_queue"]),
        ("Demo Orders", summary["orders"]),
    ])}
    <div class="card"><h2>Pipeline</h2><div class="pipeline">{pipeline}</div></div>
    <div class="card"><h2>Leads</h2><table><tr><th>Contact</th><th>Phone</th><th>Stage</th><th>Status</th></tr>{lead_rows}</table></div>
    <div class="card"><h2>Patient Search</h2><table><tr><th>Code</th><th>Name</th><th>Phone</th></tr>{patient_rows}</table></div>
    <div class="card"><h2>Upcoming Appointments</h2><p class="muted">Demo walk-in and home collection slots for today and tomorrow.</p>
    <table><tr><th>Patient</th><th>Slot</th><th>Status</th></tr>
    {''.join(f"<tr><td>{p.full_name}</td><td>Today 09:{(i+1)*10:02d}</td><td>Scheduled</td></tr>" for i, p in enumerate(patients[:5])) or "<tr><td colspan='3'>No appointments scheduled.</td></tr>"}
    </table></div>
    <div class="card"><h2>Latest Orders</h2><table><tr><th>Order</th><th>Patient</th><th>Status</th></tr>{order_rows}</table></div>
    """


def build_logistics_body() -> str:
    from app.models.driver import Driver
    from app.models.home_collection import HomeCollection
    from app.models.sample_collection import SampleCollection
    from app.models.shipment import Shipment
    from app.models.transport_box import TransportBox

    summary = seeded_summary()
    collectors = safe_query(Driver, filter_like=("driver_code", "DEMO-COL-"), limit=20)
    collector_rows = "".join(
        f"<tr><td>{c.driver_code}</td><td>{c.full_name}</td><td>10.04{i}, 105.74{i}</td>"
        f"<td>4.2°C</td><td>{c.vehicle_no or 'DEMO-VAN'}</td><td>{c.status}</td></tr>"
        for i, c in enumerate(collectors[:10], start=1)
    ) or "<tr><td colspan='6'>No collectors seeded.</td></tr>"

    boxes = safe_query(TransportBox, limit=10) if table_exists_name("transport_boxes") else []
    if not boxes:
        box_rows = "<tr><td>BOX-DEMO-001</td><td>4.0°C</td><td>NORMAL</td><td>GPS placeholder</td></tr>"
    else:
        box_rows = "".join(
            f"<tr><td>{b.box_code}</td><td>{b.temperature}°C</td><td>{b.alert_status}</td><td>{b.latitude or '—'}, {b.longitude or '—'}</td></tr>"
            for b in boxes[:8]
        )

    pickup_rows = ""
    if table_exists_name("home_collections"):
        jobs = safe_query(HomeCollection, limit=10)
        for job in jobs:
            pickup_rows += f"<tr><td>{job.patient_id}</td><td>{job.address or 'Demo address'}</td><td>{job.scheduled_time or 'Today'}</td><td>{job.status}</td></tr>"
    if not pickup_rows and table_exists_name("sample_collections"):
        for item in safe_query(SampleCollection, limit=10):
            pickup_rows += f"<tr><td>{item.order_id}</td><td>Demo pickup address</td><td>Today</td><td>{item.status}</td></tr>"
    pickup_rows = pickup_rows or "<tr><td colspan='4'>No pickup queue items.</td></tr>"

    route_rows = "".join(
        f"<tr><td>Route {i}</td><td>{c.full_name}</td><td>08:{i*10:02d}</td><td>{45 + i * 8} min</td><td>{c.vehicle_no or 'DEMO-VAN'}</td></tr>"
        for i, c in enumerate(collectors[:5], start=1)
    ) or "<tr><td colspan='5'>No routes planned.</td></tr>"

    return f"""
    {page_header("Logistics Dashboard", "Collectors, cold-chain boxes, pickup queue, and today's routes.")}
    {metric_cards([
        ("Collectors", len(collectors)),
        ("Sample Boxes", len(boxes) or 1),
        ("Pickup Queue", pickup_rows.count("<tr>") - 1 if pickup_rows else 0),
        ("Demo Orders", summary["orders"]),
    ])}
    <div class="card"><h2>Collector List</h2><table><tr><th>Code</th><th>Name</th><th>GPS</th><th>Temp</th><th>Vehicle</th><th>Status</th></tr>{collector_rows}</table></div>
    <div class="card"><h2>Sample Boxes</h2><table><tr><th>Box</th><th>Temperature</th><th>Alert</th><th>GPS</th></tr>{box_rows}</table></div>
    <div class="card"><h2>Pickup Queue</h2><table><tr><th>Ref</th><th>Address</th><th>Schedule</th><th>Status</th></tr>{pickup_rows}</table></div>
    <div class="card"><h2>Today's Route</h2><table><tr><th>Route</th><th>Collector</th><th>Start</th><th>ETA</th><th>Vehicle</th></tr>{route_rows}</table></div>
    <div class="card links"><a href="/logistics/dispatch">Dispatch Center</a><a href="/iot-box">IoT Boxes</a><a href="/shipments">Shipments</a></div>
    """


def build_reception_body() -> str:
    from app.models.invoice import Invoice
    from app.models.order import Order
    from app.models.patient import Patient

    summary = seeded_summary()
    status = system_status()
    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=10)
    orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=10)

    walk_in = "".join(
        f"<tr><td>{p.patient_code}</td><td>{p.full_name}</td><td>Waiting</td><td>{(i % 3) + 5} min</td></tr>"
        for i, p in enumerate(patients[:6])
    ) or "<tr><td colspan='4'>No walk-in queue.</td></tr>"

    appts = "".join(
        f"<tr><td>{p.full_name}</td><td>Today {(9 + i):02d}:00</td><td>Check-in</td></tr>"
        for i, p in enumerate(patients[:5])
    ) or "<tr><td colspan='3'>No appointments.</td></tr>"

    payment_rows = ""
    if table_exists_name("invoices"):
        from app.models.invoice import Invoice as Inv

        for inv in safe_query(Inv, filter_like=("invoice_no", "DEMO-INV-"), limit=8):
            payment_rows += f"<tr><td>{inv.invoice_no}</td><td>{inv.payment_status}</td><td>{inv.total_amount or 0:,.0f}</td></tr>"
    payment_rows = payment_rows or "<tr><td colspan='3'>No invoices found.</td></tr>"

    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td><td>{o.total_amount or 0}</td></tr>"
        for o in orders
    ) or "<tr><td colspan='4'>No orders found.</td></tr>"

    pending_collection = sum(1 for o in orders if (o.status or "").upper() in {"PENDING", "CREATED", "AWAITING_COLLECTION"})

    from app.web.demo_pilot_lib import reception_workflow_path

    return f"""
    {page_header("Reception Dashboard", "Front desk queue, appointments, registration, and payment status.")}
    <div class="card"><h2>Operational Workflow</h2>{reception_workflow_path(layout="horizontal", active="Reception")}</div>
    {metric_cards([
        ("Walk-in Queue", min(len(patients), 6)),
        ("Appointments", min(len(patients), 5)),
        ("New Registration", summary["patients"]),
        ("Today's Orders", summary["orders"]),
        ("Pending Collection", pending_collection or min(len(orders), 8)),
        ("Payment Pending", payment_rows.count("UNPAID")),
    ])}
    <div class="card"><h2>Walk-in Queue</h2><table><tr><th>Code</th><th>Name</th><th>Status</th><th>Wait</th></tr>{walk_in}</table></div>
    <div class="card"><h2>Appointments</h2><table><tr><th>Patient</th><th>Time</th><th>Status</th></tr>{appts}</table></div>
    <div class="card"><h2>Payment Status</h2><table><tr><th>Invoice</th><th>Status</th><th>Amount</th></tr>{payment_rows}</table></div>
    <div class="card"><h2>Today's Orders</h2><table><tr><th>Order</th><th>Patient</th><th>Status</th><th>Amount</th></tr>{order_rows}</table></div>
    <div class="card"><h2>System Status</h2>{system_status_cards(status)}</div>
    <div class="card links"><a href="/patients">Patient Registry</a><a href="/orders/new">New Order</a><a href="/demo-accounts">Demo Accounts</a></div>
    """


def build_doctor_workbench_body() -> str:
    from app.models.doctor_profile import DoctorProfile
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.test_result import TestResult

    summary = seeded_summary()
    doctors = safe_query(DoctorProfile, filter_like=("doctor_code", "DEMO-DOC-"), limit=10)
    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=10)
    orders = safe_query(Order, filter_like=("order_code", DEMO_ORDER_PREFIX), limit=10)

    patient_rows = "".join(
        f"<tr><td>{p.patient_code}</td><td>{p.full_name}</td><td>{p.phone or ''}</td></tr>" for p in patients
    ) or "<tr><td colspan='3'>No patients.</td></tr>"

    pending = critical = released = 0
    result_rows = ""
    if table_exists_name("test_results"):
        results = safe_query(TestResult, limit=20)
        pending = sum(1 for r in results if (r.approval_status or "") == "PENDING")
        critical = sum(1 for r in results if (r.flag or "") == "CRITICAL")
        released = sum(1 for r in results if (r.approval_status or "") == "APPROVED")
        for r in results[:10]:
            result_rows += f"<tr><td>{r.test_name or 'Demo Test'}</td><td>{r.approval_status}</td><td>{r.flag or 'NORMAL'}</td><td><a href='/results/report/demo'>PDF</a></td></tr>"
    result_rows = result_rows or "<tr><td colspan='4'>No results seeded yet.</td></tr>"

    return f"""
    {page_header("Doctor Workbench", "Patient list, pending review, critical results, and report release.")}
    {metric_cards([
        ("Patients", len(patients)),
        ("Pending Review", pending),
        ("Critical Results", critical),
        ("Released Reports", released),
    ])}
    <div class="card"><h2>Patient List</h2><table><tr><th>Code</th><th>Name</th><th>Phone</th></tr>{patient_rows}</table></div>
    <div class="card"><h2>Pending Review / Critical / Released</h2><table><tr><th>Test</th><th>Status</th><th>Flag</th><th>PDF</th></tr>{result_rows}</table></div>
    <div class="card"><h2>AI Interpretation</h2><p class="muted">Placeholder — AI-assisted result interpretation will appear here during pilot review.</p></div>
    <div class="card"><h2>Recent Orders</h2><table><tr><th>Order</th><th>Patient</th><th>Status</th></tr>
    {''.join(f"<tr><td>{o.order_code}</td><td>{o.patient_id}</td><td>{o.status}</td></tr>" for o in orders) or "<tr><td colspan='3'>No orders.</td></tr>"}
    </table></div>
    <div class="card links"><a href="/doctor/dashboard">Full Doctor Portal</a><a href="/workflow-demo">Workflow</a></div>
    """


def build_patient_portal_body() -> str:
    from app.models.invoice import Invoice
    from app.models.notification import Notification
    from app.models.order import Order
    from app.models.patient import Patient
    from app.models.test_result import TestResult

    summary = seeded_summary()
    patients = safe_query(Patient, filter_like=("patient_code", DEMO_PATIENT_PREFIX), limit=10)
    first = patients[0] if patients else None
    patient_id = first.patient_code if first else None

    orders = Order.query.filter_by(patient_id=patient_id).limit(10).all() if patient_id else []
    order_rows = "".join(
        f"<tr><td>{o.order_code}</td><td>{o.status}</td><td>{o.total_amount or 0}</td></tr>" for o in orders
    ) or "<tr><td colspan='3'>No orders for demo patient.</td></tr>"

    report_rows = ""
    if table_exists_name("test_results") and orders:
        from app.models.order_item import OrderItem

        order_ids = [o.id for o in orders]
        items = OrderItem.query.filter(OrderItem.order_id.in_(order_ids)).limit(10).all() if order_ids else []
        for item in items:
            result = TestResult.query.filter_by(order_item_id=item.id).first()
            if result:
                report_rows += f"<tr><td>{result.test_name}</td><td>{result.approval_status}</td><td><a href='/results/report/demo'>Download PDF</a></td></tr>"
    report_rows = report_rows or "<tr><td colspan='3'>No reports available yet.</td></tr>"

    invoice_rows = ""
    if table_exists_name("invoices") and orders:
        for o in orders[:5]:
            inv = Invoice.query.filter_by(order_id=o.id).first()
            if inv:
                invoice_rows += f"<tr><td>{inv.invoice_no}</td><td>{inv.payment_status}</td><td>{inv.total_amount or 0:,.0f}</td></tr>"
    invoice_rows = invoice_rows or "<tr><td colspan='3'>No invoices.</td></tr>"

    notif_rows = ""
    if table_exists_name("notifications"):
        for n in safe_query(Notification, filter_like=("notification_code", "DEMO-NOT-"), limit=5):
            notif_rows += f"<tr><td>{n.subject}</td><td>{n.status}</td><td>{n.created_at or ''}</td></tr>"
    notif_rows = notif_rows or "<tr><td colspan='3'>No notifications.</td></tr>"

    patient_rows = "".join(
        f"<tr><td>{p.patient_code}</td><td>{p.full_name}</td><td><a href='/patient?patient_id={p.patient_code}'>Open</a></td></tr>"
        for p in patients
    ) or "<tr><td colspan='3'>No demo patients.</td></tr>"

    qr = first.patient_code if first else "DEMO-PAT-001"

    return f"""
    {page_header("Patient Portal", "Orders, reports, invoices, appointments, QR card, and notifications.")}
    {metric_cards([
        ("My Orders", len(orders)),
        ("Reports", report_rows.count("<tr>") - 1),
        ("Invoices", invoice_rows.count("<tr>") - 1),
        ("Notifications", notif_rows.count("<tr>") - 1),
    ])}
    <div class="card"><h2>Demo Patients</h2><table><tr><th>Code</th><th>Name</th><th>Portal</th></tr>{patient_rows}</table></div>
    <div class="card"><h2>My Orders</h2><table><tr><th>Order</th><th>Status</th><th>Amount</th></tr>{order_rows}</table></div>
    <div class="card"><h2>Reports</h2><table><tr><th>Test</th><th>Status</th><th>Download</th></tr>{report_rows}</table></div>
    <div class="card"><h2>Invoices</h2><table><tr><th>Invoice</th><th>Payment</th><th>Amount</th></tr>{invoice_rows}</table></div>
    <div class="card"><h2>Appointments</h2><p class="muted">Upcoming home collection and clinic visits for {first.full_name if first else 'demo patient'}.</p>
    <table><tr><th>Type</th><th>When</th><th>Status</th></tr><tr><td>Home Collection</td><td>Tomorrow 09:00</td><td>Scheduled</td></tr></table></div>
    <div class="card"><h2>QR Card</h2><p><strong>Patient Code:</strong> {qr}</p><p class="muted">QR placeholder for check-in and sample tracking.</p></div>
    <div class="card"><h2>Medical History</h2><p class="muted">Timeline available at <a href="/patient/timeline?patient_id={qr}">/patient/timeline</a></p></div>
    <div class="card"><h2>Notifications</h2><table><tr><th>Subject</th><th>Status</th><th>When</th></tr>{notif_rows}</table></div>
    """


def workflow_timeline_path(*, active: str | None = None) -> str:
    parts: list[str] = []
    for index, (label, href, detail) in enumerate(WORKFLOW_TIMELINE):
        active_class = " active" if active and label == active else ""
        parts.append(
            f"""
            <div class="workflow-step timeline-step{active_class}" data-step="{index + 1}">
                <a href="{href}">
                    <strong>{label}</strong>
                    <div class="muted">{detail}</div>
                </a>
            </div>
            """
        )
        if index < len(WORKFLOW_TIMELINE) - 1:
            parts.append('<div class="workflow-arrow">↓</div>')
    return f'<div class="workflow-path timeline">{"".join(parts)}</div>'


def build_workflow_demo_body() -> str:
    from app.models.invoice import Invoice
    from app.models.notification import Notification
    from app.models.order_item import OrderItem
    from app.models.sample_collection import SampleCollection
    from app.models.test_result import TestResult

    summary = seeded_summary()
    ids = _demo_order_ids()
    order_items = OrderItem.query.filter(OrderItem.order_id.in_(ids)).count() if ids else 0
    collections = safe_count(SampleCollection) if table_exists_name("sample_collections") else 0
    results = safe_count(TestResult) if table_exists_name("test_results") else 0
    invoices = safe_count(Invoice, prefix="DEMO-INV-", field="invoice_no") if table_exists_name("invoices") else 0
    notifications = safe_count(Notification, prefix="DEMO-NOT-", field="notification_code") if table_exists_name("notifications") else 0

    counts = {
        "Registration": summary["patients"],
        "Order": summary["orders"],
        "Payment": invoices,
        "Collection": collections,
        "Transport": min(collections, 40),
        "Laboratory": results,
        "Verification": results,
        "Doctor Approval": max(0, results // 2),
        "Release": max(0, results // 3),
        "Notification": notifications,
    }
    step_metrics = "".join(
        f'<div class="step"><strong>{name}</strong><div>{counts.get(name, 0)}</div></div>'
        for name, _, _ in WORKFLOW_TIMELINE
    )

    return f"""
    {page_header("Workflow Timeline", "Interactive end-to-end pilot path from registration through notification.")}
    <div class="card"><h2>Interactive Timeline</h2><p class="muted">Click each step to navigate the operational screen.</p>{workflow_timeline_path()}</div>
    <div class="card"><h2>Step Counts</h2><div class="steps">{step_metrics}</div></div>
    """


def _bar_chart(title: str, items: list[tuple[str, int | float]]) -> str:
    if not items:
        return f'<div class="chart-card"><h3>{title}</h3><p class="muted">No data</p></div>'
    max_val = max(v for _, v in items) or 1
    bars = ""
    for label, value in items:
        height = max(8, int((value / max_val) * 100))
        bars += f'<div class="bar-item"><div class="bar" style="height:{height}px"></div><span>{label}</span><small>{value}</small></div>'
    return f'<div class="chart-card"><h3>{title}</h3><div class="bar-chart">{bars}</div></div>'
