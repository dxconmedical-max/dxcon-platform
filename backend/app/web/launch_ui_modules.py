"""Launch UI Sprint 2/3 — functional module pages with real demo data."""

from __future__ import annotations

from typing import Callable

import html as html_module

from app.web.launch_ui_actions import (
    action_button,
    action_button_row,
    workflow_stage_cards,
)
from app.web.launch_ui_data import (
    get_finance_summary,
    get_order_detail,
    get_patient_detail,
    get_queue_summary,
    get_recent_collections,
    get_recent_invoices,
    get_recent_orders,
    get_recent_patients,
    get_recent_reports,
    get_recent_samples,
    get_recent_tests,
    get_report_detail,
)
from app.web.launch_ui_lib import (
    DEMO_ROLE_DASHBOARDS,
    action_grid,
    back_nav,
    breadcrumbs,
    demo_form_card,
    empty_state,
    metric_cards,
    module_intro,
    query_string_note,
    queue_stage_cards,
    real_form_card,
    status_badge,
    table_html,
    table_section,
    timeline_section,
    workflow_action_form,
)

MODULE_ROUTES: tuple[str, ...] = (
    "/app/orders",
    "/app/orders/new",
    "/app/patients",
    "/app/patients/new",
    "/app/reports",
    "/app/finance",
    "/app/logistics",
    "/app/reception/queue",
    "/app/ai",
    "/app/samples",
    "/app/samples/accession",
    "/app/lab/testing",
    "/app/lab/qc",
    "/app/collections",
    "/app/collections/route",
    "/app/iot",
    "/app/samples/chain-of-custody",
    "/app/patient/profile",
    "/app/patient/orders",
    "/app/patient/reports",
    "/app/patient/qr",
    "/app/patient/invoices",
    "/app/patient/notifications",
)

ROLE_DEMO_TARGETS = DEMO_ROLE_DASHBOARDS
MODULE_SPECS: list[tuple[str, str, Callable[[], str]]] = []


def _register(title: str, path: str):
    def decorator(fn: Callable[[], str]):
        MODULE_SPECS.append((path, title, fn))
        return fn

    return decorator


def _h(value: str) -> str:
    return html_module.escape(str(value))


def patient_detail_body(patient_key: str) -> str:
    patient = get_patient_detail(patient_key)
    pk = _h(patient_key)
    order_rows = []
    for order in patient.get("orders", []):
        key = _h(order["order_code"])
        order_rows.append([
            f'<a href="/app/orders/{key}">{key}</a>',
            status_badge(order.get("status", "PENDING")),
            f"${order.get('total_amount', 0):,.0f}",
        ])
    invoice_rows = []
    for inv in patient.get("invoices", []):
        invoice_rows.append([_h(inv.get("invoice_no", "")), status_badge(inv.get("status", "unpaid"))])
    report_rows = []
    for rep in patient.get("reports", []):
        rk = _h(rep.get("result_code", rep.get("id", "")))
        report_rows.append([
            f'<a href="/app/reports/{rk}">{rk}</a>',
            status_badge(rep.get("status", "pending")),
        ])
    if not report_rows:
        for label, status in [("CBC", "RELEASED"), ("Lipid panel", "PENDING")]:
            report_rows.append([label, status_badge(status)])
    qr = _h(patient.get("qr_payload", f"dxcon:patient:{pk}"))
    return (
        breadcrumbs([("Patients", "/app/patients"), (patient["full_name"], f"/app/patients/{pk}")])
        + metric_cards([
            ("Code", patient["patient_code"]),
            ("Phone", patient["phone"]),
            ("Gender", patient["gender"]),
        ])
        + table_section("Demographics & contact", ["Field", "Value"], [
            ["Email", patient.get("email", "—")],
            ["Address", patient.get("address", "—")],
            ["Phone", patient["phone"]],
        ])
        + f'<div class="launch-card"><h3>QR health card</h3><div class="launch-chart">{qr}</div>'
        + table_html("Order history", ["Order", "Status", "Amount"], order_rows or [])
        + table_html("Report history", ["Report", "Status"], report_rows)
        + table_html("Invoice history", ["Invoice", "Amount", "Status"], invoice_rows)
        + action_button_row([
            action_button("Create new order", "create-demo-order", patient_key, "patient", f"/app/patients/{pk}", primary=True),
            action_button("Check in", "check-in-patient", patient_key, "patient", f"/app/patients/{pk}"),
            action_button("Notify patient", "send-notification", patient_key, "patient", f"/app/patients/{pk}"),
        ])
        + real_form_card(
            "Create real order",
            "/app/business/orders/create",
            [("patient_code", "Patient code", patient_key)],
            cancel_href=f"/app/patients/{pk}",
            submit_label="Create order",
        )
    )


def order_detail_body(order_key: str) -> str:
    order = get_order_detail(order_key)
    patient_key = order.get("patient_id") or order.get("patient_code", "")
    pk = _h(patient_key)
    ok = _h(order_key)
    ret = f"/app/orders/{ok}"
    is_biz = bool(order.get("items")) or order.get("status", "").lower() in {
        "draft", "payment_pending", "paid", "sampling", "collected", "in_transit",
        "lab_received", "testing", "pending_review", "approved", "released",
    }
    stages = [
        ("Payment", order.get("invoice", {}).get("status", "—").upper() if order.get("invoice") else "—", "—"),
        ("Collection", (order.get("collection") or {}).get("status", "—").upper(), "—"),
        ("Lab", order.get("status", "—").upper(), "—"),
        ("Report", (order.get("result") or {}).get("status", "—").upper(), "—"),
    ]
    test_rows = []
    for item in order.get("items", []):
        test_rows.append([_h(item.get("test_name", "")), f"${item.get('line_total', 0):,.0f}"])
    if not test_rows:
        test_rows = [["Blood panel", status_badge("TESTING")], ["Glucose", status_badge("QUEUED")]]
    timeline = order.get("timeline", [])
    if timeline and isinstance(timeline[0], dict):
        timeline_pairs = [(t.get("label", ""), t.get("time", "—")) for t in timeline]
    else:
        timeline_pairs = timeline or [
            ("Ordered", "08:00"), ("Sample collected", "09:15"), ("In lab", "10:30"), ("Report", "Pending review"),
        ]
    real_actions = ""
    if is_biz:
        real_actions = (
            '<div class="launch-card"><h3>Workflow actions (live)</h3><div class="launch-footer-actions">'
            + workflow_action_form(f"/app/business/orders/{ok}/mark-paid", ok, "Mark paid", [("payment_method", "Method", "cash")])
            + workflow_action_form(f"/app/business/orders/{ok}/collection", ok, "Assign collector", [
                ("collector_name", "Collector", "Demo Collector"),
                ("pickup_address", "Address", "District 1, HCMC"),
            ])
            + workflow_action_form(f"/app/business/orders/{ok}/collect", ok, "Collect sample")
            + workflow_action_form(f"/app/business/orders/{ok}/receive", ok, "Receive at lab", [("received_by", "Received by", "Lab tech")])
            + workflow_action_form(f"/app/business/orders/{ok}/enter-results", ok, "Enter results")
            + workflow_action_form(f"/app/business/orders/{ok}/approve", ok, "Approve", [("doctor_note", "Note", "Reviewed")])
            + workflow_action_form(f"/app/business/orders/{ok}/release", ok, "Release report")
            + "</div></div>"
        )
    demo_actions = action_button_row([
        action_button("Mark paid", "mark-paid", order_key, "order", ret),
        action_button("Assign collector", "assign-collector", order_key, "order", ret),
        action_button("Receive sample", "receive-sample", order_key, "sample", ret),
        action_button("Start testing", "start-testing", order_key, "sample", ret),
        action_button("Approve report", "doctor-approve", order_key, "report", ret, primary=True),
        action_button("Release report", "release-report", order_key, "report", ret),
    ])
    return (
        breadcrumbs([("Orders", "/app/orders"), (order["order_code"], ret)])
        + metric_cards([
            ("Status", order["status"]),
            ("Amount", f"${order.get('total_amount', 0):,.0f}"),
            ("Patient", order["patient_name"]),
        ])
        + f'<div class="launch-card"><h3>Patient summary</h3><p><a href="/app/patients/{pk}">{_h(order["patient_name"])}</a> · Code {pk}</p></div>'
        + workflow_stage_cards(stages)
        + timeline_section("Workflow timeline", timeline_pairs)
        + table_html("Ordered tests", ["Test", "Amount"] if is_biz else ["Test", "Status"], test_rows)
        + real_actions
        + (demo_actions if not is_biz else "")
    )


def report_detail_body(report_key: str) -> str:
    report = get_report_detail(report_key)
    rk = _h(report_key)
    ret = f"/app/reports/{rk}"
    flag = report.get("flag", "NORMAL")
    return (
        breadcrumbs([("Reports", "/app/reports"), (report["test_name"], ret)])
        + metric_cards([
            ("Result", f"{report['result_value']} {report.get('unit', '')}".strip()),
            ("Reference", report.get("reference_range", "—")),
            ("Flag", flag),
        ])
        + module_intro("Result preview", f"Status: {report.get('approval_status', 'PENDING')}")
        + table_html("Abnormal flags", ["Marker", "Value", "Flag"], [
            [_h(report["test_name"]), _h(str(report["result_value"])), status_badge(flag)],
        ])
        + f'<div class="launch-card"><h3>AI interpretation (advisory)</h3><p>{_h(report.get("interpretation", ""))}</p>'
        + '<p class="launch-hint">Human clinician review required before release.</p></div>'
        + '<div class="launch-card launch-alert"><h3>Doctor review</h3><p>Sign-off required for patient portal release. Demo actions below simulate approval workflow.</p></div>'
        + '<div class="launch-card"><h3>PDF report</h3>'
        + (f'<a class="launch-btn" href="/app/business/reports/{rk}/print" target="_blank">Open HTML/PDF report</a>'
           if report.get("html_content") else
           '<div class="launch-chart">Report not released yet</div>')
        + '</div>'
        + action_button_row([
            action_button("Doctor approve", "doctor-approve", report_key, "report", ret, primary=True),
            action_button("Release to patient", "release-report", report_key, "report", ret),
            action_button("Send notification", "send-notification", report_key, "notification", ret),
        ])
    )


DETAIL_ROUTE_BUILDERS = (
    ("/app/patients/<patient_key>", patient_detail_body),
    ("/app/orders/<order_key>", order_detail_body),
    ("/app/reports/<report_key>", report_detail_body),
)


@_register("Orders", "/app/orders")
def orders_body() -> str:
    rows = []
    for order in get_recent_orders(12):
        key = _h(order["order_code"])
        patient_key = _h(order.get("patient_id", ""))
        rows.append([
            f'<a href="/app/orders/{key}">{key}</a>',
            f'<a href="/app/patients/{patient_key}">{_h(order["patient_name"])}</a>',
            status_badge(order["status"]),
            f"${order['total_amount']:,.0f}",
            f'<a class="launch-btn-outline launch-btn-sm" href="/app/orders/{key}">Open</a>',
        ])
    return (
        back_nav("/app/executive", "Executive dashboard")
        + module_intro("Orders", "Active diagnostic orders across clinics and home collection.")
        + table_html("Recent orders", ["Order", "Patient", "Status", "Amount", "Action"], rows)
        + action_grid([("Create order", "/app/orders/new", "New walk-in or referral order")])
    )


@_register("New Order", "/app/orders/new")
def orders_new_body() -> str:
    from app.business_engine.service import ensure_test_catalog_seed
    from app.extensions.db import db

    ensure_test_catalog_seed()
    db.session.commit()
    patients = get_recent_patients(10)
    tests = get_recent_tests(10)
    patient_options = []
    for p in patients:
        patient_options.append(("patient_code", f"{p['full_name']} ({p['patient_code']})", p["patient_code"]))
    default_patient = patients[0]["patient_code"] if patients else ""
    fields = [("patient_code", "Patient code", default_patient), ("discount", "Discount", "0"), ("note", "Note", "")]
    for test in tests[:5]:
        label = f"{test['name']} — ${test.get('price', 0):,.0f}"
        fields.append(("test_catalog_id", label, test.get("id", test.get("code", ""))))
    return (
        back_nav("/app/orders", "Orders")
        + breadcrumbs([("Orders", "/app/orders"), ("New order", "/app/orders/new")])
        + real_form_card("Create order (live)", "/app/business/orders/create", fields, cancel_href="/app/orders", submit_label="Create order")
        + demo_form_card(
            "Demo preview",
            [
                ("Patient", patients[0]["full_name"] if patients else "Demo Patient"),
                ("Test package", tests[0]["name"] if tests else "Blood panel"),
                ("Collection", "Clinic walk-in"),
                ("Payment method", "Cash / Card"),
            ],
            "/app/orders",
            "/app/orders",
        )
    )


@_register("Patients", "/app/patients")
def patients_body() -> str:
    rows = []
    for patient in get_recent_patients(15):
        key = _h(patient["patient_code"])
        rows.append([
            key,
            _h(patient["full_name"]),
            _h(patient["phone"]),
            _h(patient["gender"]),
            f'<a class="launch-btn-outline launch-btn-sm" href="/app/patients/{key}">View</a>',
        ])
    return (
        back_nav("/app/executive", "Executive dashboard")
        + module_intro("Patients", "Search and manage patient records.")
        + '<div class="launch-card"><input class="launch-field" placeholder="Search by name, phone, or patient code"></div>'
        + table_html("Patient directory", ["Code", "Name", "Phone", "Gender", "Action"], rows)
        + action_grid([("New registration", "/app/patients/new", "Register walk-in patient")])
    )


@_register("New Patient", "/app/patients/new")
def patients_new_body() -> str:
    return (
        back_nav("/app/patients", "Patients")
        + breadcrumbs([("Patients", "/app/patients"), ("New registration", "/app/patients/new")])
        + real_form_card(
            "Patient registration (live)",
            "/app/business/patients/create",
            [
                ("full_name", "Full name", ""),
                ("phone", "Phone", ""),
                ("email", "Email", ""),
                ("gender", "Gender", ""),
                ("date_of_birth", "Date of birth", ""),
                ("national_id", "National ID", ""),
                ("address", "Address", ""),
            ],
            cancel_href="/app/patients",
            submit_label="Register patient",
        )
        + demo_form_card(
            "Demo preview",
            [
                ("Full name", "Nguyen Van Demo"),
                ("Phone", "0901234567"),
                ("Email", "patient@demo.dxcon.test"),
                ("Gender", "Male"),
                ("Address", "District 1, Ho Chi Minh City"),
            ],
            "/app/patients",
            "/app/patients",
        )
    )


@_register("Reports", "/app/reports")
def reports_body() -> str:
    rows = []
    for report in get_recent_reports(12):
        key = _h(report["id"])
        rows.append([
            _h(report["test_name"]),
            _h(report["patient_name"]),
            status_badge(report["approval_status"]),
            status_badge(report["flag"]),
            f'<a class="launch-btn-outline launch-btn-sm" href="/app/reports/{key}">Review</a>',
        ])
    return (
        back_nav("/app/doctor", "Doctor workbench")
        + module_intro("Reports & results", "Validated results awaiting review or release.")
        + query_string_note()
        + table_html("Report queue", ["Test", "Patient", "Status", "Flag", "Action"], rows)
    )


@_register("Finance", "/app/finance")
def finance_body() -> str:
    summary = get_finance_summary()
    invoice_rows = []
    for invoice in get_recent_invoices(10):
        invoice_rows.append([
            _h(invoice["invoice_no"]),
            f"${invoice['amount']:,.0f}",
            status_badge(invoice["status"]),
            "Bank transfer",
        ])
    return (
        back_nav("/app/executive", "Executive dashboard")
        + module_intro("Finance", "Invoices, payments, and revenue summary.")
        + metric_cards([
            ("Revenue", f"${summary['revenue']:,.0f}"),
            ("Paid", summary["paid_count"]),
            ("Pending", summary["pending_count"]),
            ("Invoices", summary["invoice_total"]),
        ])
        + table_html("Invoices", ["Invoice", "Amount", "Status", "Method"], invoice_rows)
    )


@_register("Logistics", "/app/logistics")
def logistics_body() -> str:
    from app.web.launch_ui_data import get_demo_counts

    counts = get_demo_counts()
    rows = []
    for sample in get_recent_samples(8):
        rows.append([_h(sample["sample_code"]), status_badge(sample["status"]), "In transit", status_badge("OK")])
    return (
        back_nav("/app/executive", "Executive dashboard")
        + module_intro("Logistics", "Route overview, in-transit samples, and SLA tracking.")
        + metric_cards([("In transit", counts["samples_in_transit"]), ("SLA", "98.6%"), ("Collectors active", "3")])
        + table_html("In-transit samples", ["Sample", "Status", "Route", "SLA"], rows)
        + action_grid([
            ("Collector queue", "/app/collections", "Pickup jobs"),
            ("Route planner", "/app/collections/route", "Today's route"),
            ("IoT monitoring", "/app/iot", "Cold chain"),
        ])
    )


@_register("Reception Queue", "/app/reception/queue")
def reception_queue_body() -> str:
    stages = get_queue_summary()
    return (
        back_nav("/app/reception", "Reception")
        + module_intro("Waiting queue", "Live service desk queue by stage.")
        + queue_stage_cards(stages)
        + table_html("Queue detail", ["Token", "Patient", "Stage", "Wait"], [
            ["Q-101", "Nguyen Van A", status_badge("WAITING"), "12m"],
            ["Q-102", "Le Van C", status_badge("CHECKED_IN"), "5m"],
            ["Q-103", "Tran Thi B", status_badge("SAMPLING"), "—"],
            ["Q-100", "Demo Patient", status_badge("COMPLETED"), "—"],
        ])
    )


@_register("AI Copilot", "/app/ai")
def ai_body() -> str:
    return (
        back_nav("/app/doctor", "Doctor workbench")
        + module_intro("AI interpretation", "Advisory only — clinician approval required before release.")
        + '<div class="launch-card launch-alert"><strong>Safety disclaimer</strong><p>AI output is not a diagnosis. All results require licensed medical review.</p></div>'
        + '<div class="launch-card"><h3>Sample explanation</h3><p>Glucose 180 mg/dL is above the reference range. This may indicate hyperglycemia. Correlate with fasting status, medications, and symptoms.</p></div>'
        + metric_cards([("Confidence", "87%"), ("PHI redacted", "Yes"), ("Human review", "Required")])
    )


@_register("Samples", "/app/samples")
def samples_body() -> str:
    rows = []
    for sample in get_recent_samples(12):
        rows.append([_h(sample["sample_code"]), status_badge(sample["status"]), _h(sample.get("updated_at", "—"))])
    return (
        back_nav("/app/lab", "Lab dashboard")
        + module_intro("Sample queue", "Specimens across ordered → collected → in transit → received → testing → completed.")
        + table_html("Sample queue", ["Sample", "Status", "Updated"], rows)
        + action_grid([
            ("Accession", "/app/samples/accession", "Receive in lab"),
            ("Chain of custody", "/app/samples/chain-of-custody", "Scan log"),
        ])
    )


@_register("Sample Accession", "/app/samples/accession")
def samples_accession_body() -> str:
    return (
        back_nav("/app/samples", "Samples")
        + module_intro("Accession", "Register received specimens into LIS.")
        + demo_form_card(
            "Receive sample",
            [("Barcode", "BC-883921"), ("Sample type", "Blood"), ("Collector", "Demo Collector"), ("Temperature", "4.2°C")],
            "/app/samples",
            "/app/samples",
        )
    )


@_register("Lab Testing", "/app/lab/testing")
def lab_testing_body() -> str:
    tests = get_recent_tests(5)
    rows = [[_h(t["name"]), "Sysmex / Cobas", status_badge("TESTING"), _h(str(t["turnaround_hours"]) + "h")] for t in tests]
    return (
        back_nav("/app/lab", "Lab dashboard")
        + module_intro("Testing", "Analyzers and manual bench work in progress.")
        + table_html("Tests in progress", ["Test", "Instrument", "Status", "TAT"], rows)
        + '<div class="launch-card"><h3>Result entry</h3><p>Manual result entry placeholder — connect LIS integration for production.</p></div>'
    )


@_register("Lab QC", "/app/lab/qc")
def lab_qc_body() -> str:
    return (
        back_nav("/app/lab", "Lab dashboard")
        + module_intro("Quality control", "Daily QC with abnormal flag monitoring.")
        + queue_stage_cards({"passed": 2, "running": 1, "abnormal_flags": 0})
        + table_html("QC runs", ["Run", "Level", "Status", "Flag"], [
            ["QC-01", "Normal", status_badge("PASS"), status_badge("OK")],
            ["QC-02", "High", status_badge("PASS"), status_badge("OK")],
        ])
    )


@_register("Collections", "/app/collections")
def collections_body() -> str:
    rows = []
    for job in get_recent_collections(10):
        rows.append([
            _h(job["job_code"]),
            _h(job["patient_name"]),
            _h(job["address"]),
            status_badge(job["status"]),
            f'<a class="launch-btn-outline launch-btn-sm" href="/app/collections/route">Route</a>',
        ])
    return (
        back_nav("/app/collector", "Collector dashboard")
        + module_intro("Pickup queue", "Home and clinic collection jobs.")
        + table_html("Pickup queue", ["Job", "Patient", "Address", "Status", "Action"], rows)
    )


@_register("Collection Route", "/app/collections/route")
def collections_route_body() -> str:
    return (
        back_nav("/app/collections", "Collections")
        + module_intro("Route", "Optimized collection route with ETA cards.")
        + metric_cards([("Stops", "3"), ("Completed", "1"), ("Next ETA", "30m")])
        + timeline_section("Route timeline", [
            ("Clinic A", "09:00 — Completed"),
            ("Patient home B", "10:30 — Next"),
            ("Clinic C", "13:00 — Scheduled"),
        ])
        + '<div class="launch-card"><h3>Google Maps</h3><div class="launch-chart">Map placeholder · integrate Maps SDK</div></div>'
    )


@_register("IoT Cold Chain", "/app/iot")
def iot_body() -> str:
    return (
        back_nav("/app/collector", "Collector dashboard")
        + module_intro("Cold chain IoT", "Temperature, GPS, shock, and battery telemetry.")
        + table_html("Cold boxes", ["Device", "Temp", "GPS", "Shock", "Battery", "Alert"], [
            ["BOX-01", "4.2°C", status_badge("OK"), status_badge("OK"), "87%", status_badge("OK")],
            ["BOX-02", "5.1°C", status_badge("OK"), status_badge("OK"), "72%", status_badge("WARNING")],
        ])
    )


@_register("Chain of Custody", "/app/samples/chain-of-custody")
def chain_of_custody_body() -> str:
    stages = [
        ("Collection", "COMPLETED", "08:15"),
        ("Packed", "COMPLETED", "08:30"),
        ("In transit", "IN_TRANSIT", "08:45"),
        ("Received by lab", "RECEIVED", "10:02"),
        ("Accessioned", "ACCESSIONED", "10:18"),
        ("Tested", "TESTING", "11:00"),
        ("Released", "PENDING", "—"),
    ]
    return (
        back_nav("/app/collector", "Collector dashboard")
        + module_intro("Chain of custody", "End-to-end sample custody with cold chain monitoring.")
        + workflow_stage_cards(stages)
        + metric_cards([("Cold box", "BOX-01"), ("Temperature", "4.2°C"), ("Alert", "OK")])
        + table_html("Custody scan log", ["Event", "Actor", "Time", "Status"], [
            ["Collected", "Collector Demo", "08:15", status_badge("OK")],
            ["Packed in cold box", "BOX-01", "08:30", status_badge("OK")],
            ["In transit", "Route A", "08:45", status_badge("IN_TRANSIT")],
            ["Lab received", "Accession desk", "10:02", status_badge("RECEIVED")],
            ["Accessioned", "Lab tech", "10:18", status_badge("ACCESSIONED")],
            ["Testing started", "Analyzer", "11:00", status_badge("TESTING")],
        ])
        + action_button_row([
            action_button("Collect sample", "collect-sample", "S-DEMO-001", "sample", "/app/samples/chain-of-custody"),
            action_button("Receive at lab", "receive-sample", "S-DEMO-001", "sample", "/app/samples/chain-of-custody", primary=True),
        ])
    )


@_register("My Profile", "/app/patient/profile")
def patient_profile_body() -> str:
    patients = get_recent_patients(1)
    patient = patients[0] if patients else {"full_name": "Demo Patient", "patient_code": "P-DEMO-001", "phone": "0901234567", "email": "patient@demo.dxcon.test", "gender": "Male", "address": "District 1"}
    return (
        back_nav("/app/patient", "Patient portal")
        + metric_cards([
            ("Name", patient["full_name"]),
            ("Code", patient["patient_code"]),
            ("Phone", patient["phone"]),
        ])
        + table_section("Contact", ["Field", "Value"], [
            ["Email", patient.get("email", "—")],
            ["Gender", patient.get("gender", "—")],
            ["Address", patient.get("address", "—")],
        ])
    )


@_register("My Orders", "/app/patient/orders")
def patient_orders_body() -> str:
    rows = []
    for order in get_recent_orders(8):
        key = _h(order["order_code"])
        rows.append([f'<a href="/app/orders/{key}">{key}</a>', _h(order.get("created_at", "—")), status_badge(order["status"])])
    return back_nav("/app/patient", "Patient portal") + table_html("My orders", ["Order", "Date", "Status"], rows)


@_register("My Reports", "/app/patient/reports")
def patient_reports_body() -> str:
    rows = []
    for report in get_recent_reports(8):
        key = _h(report["id"])
        rows.append([_h(report["test_name"]), status_badge(report["approval_status"]), f'<a href="/app/reports/{key}">View</a>'])
    return back_nav("/app/patient", "Patient portal") + table_html("My reports", ["Report", "Status", "Action"], rows)


@_register("QR Health Card", "/app/patient/qr")
def patient_qr_body() -> str:
    patients = get_recent_patients(1)
    code = patients[0]["patient_code"] if patients else "P-DEMO-001"
    return (
        back_nav("/app/patient", "Patient portal")
        + f'<div class="launch-card"><h3>QR health card</h3><div class="launch-chart">QR · {_h(code)}</div>'
        + "<p class=\"launch-hint\">Show at reception for express check-in.</p></div>"
    )


@_register("My Invoices", "/app/patient/invoices")
def patient_invoices_body() -> str:
    rows = []
    for invoice in get_recent_invoices(8):
        rows.append([_h(invoice["invoice_no"]), f"${invoice['amount']:,.0f}", status_badge(invoice["status"])])
    return back_nav("/app/patient", "Patient portal") + table_html("Invoices", ["Invoice", "Amount", "Status"], rows)


@_register("Notifications", "/app/patient/notifications")
def patient_notifications_body() -> str:
    return (
        back_nav("/app/patient", "Patient portal")
        + table_html("Notifications", ["Message", "Channel", "Time"], [
            ["Your CBC result is ready", "SMS", "2h ago"],
            ["Appointment tomorrow 09:00", "Email", "Yesterday"],
            ["Invoice INV-DEMO-002 pending", "App", "Today"],
        ])
    )
