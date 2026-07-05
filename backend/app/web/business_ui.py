"""Business engine UI routes — real POST actions."""

from __future__ import annotations

import html

from flask import Blueprint, flash, redirect, request, url_for

from app.business_engine import service as biz
from app.business_engine.service import BusinessEngineError
from app.extensions.db import db
from app.models.test_catalog import TestCatalog
from app.utils.auth import login_required
from app.web.launch_ui_lib import render_page

business_ui_bp = Blueprint("business_ui", __name__)


def _redirect_back(default: str):
    target = request.form.get("return_to") or request.args.get("return") or default
    if not target.startswith("/app/"):
        target = default
    return redirect(target)


def _error_page(title: str, message: str, back_href: str) -> str:
    body = (
        f'<div class="launch-card launch-alert"><h3>{html.escape(title)}</h3>'
        f"<p>{html.escape(message)}</p>"
        f'<a class="launch-btn" href="{html.escape(back_href)}">Go back</a></div>'
    )
    return render_page(title, body, active_nav="/app/executive")


@business_ui_bp.route("/app/business/patients/create", methods=["POST"])
@login_required
def create_patient():
    try:
        patient = biz.create_patient(
            full_name=request.form.get("full_name", ""),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            gender=request.form.get("gender"),
            date_of_birth=request.form.get("date_of_birth"),
            address=request.form.get("address"),
            national_id=request.form.get("national_id"),
        )
        db.session.commit()
        return redirect(f"/app/patients/{patient.patient_code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Patient registration failed", str(exc), "/app/patients/new"), 400


@business_ui_bp.route("/app/business/patients/<patient_code>/edit", methods=["POST"])
@login_required
def edit_patient(patient_code: str):
    try:
        biz.update_patient(
            patient_code,
            full_name=request.form.get("full_name"),
            phone=request.form.get("phone"),
            email=request.form.get("email"),
            gender=request.form.get("gender"),
            date_of_birth=request.form.get("date_of_birth"),
            address=request.form.get("address"),
            national_id=request.form.get("national_id"),
        )
        db.session.commit()
        return redirect(f"/app/patients/{patient_code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Update failed", str(exc), f"/app/patients/{patient_code}"), 400


@business_ui_bp.route("/app/business/orders/create", methods=["POST"])
@login_required
def create_order():
    try:
        biz.ensure_test_catalog_seed()
        catalog_ids = request.form.getlist("test_catalog_id")
        order = biz.create_order(
            patient_code=request.form.get("patient_code", ""),
            test_catalog_ids=catalog_ids or None,
            discount=float(request.form.get("discount") or 0),
            note=request.form.get("note"),
        )
        biz.submit_order_for_payment(order.order_code)
        db.session.commit()
        return redirect(f"/app/orders/{order.order_code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Order creation failed", str(exc), "/app/orders/new"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/mark-paid", methods=["POST"])
@login_required
def mark_paid(order_ref: str):
    try:
        biz.mark_order_paid(
            order_ref,
            payment_method=request.form.get("payment_method", "cash"),
            receipt_number=request.form.get("receipt_number"),
        )
        db.session.commit()
        return _redirect_back(f"/app/orders/{order_ref}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Payment failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/collection", methods=["POST"])
@login_required
def create_collection(order_ref: str):
    try:
        biz.create_collection_job(
            order_ref,
            collector_name=request.form.get("collector_name", ""),
            pickup_address=request.form.get("pickup_address", ""),
        )
        db.session.commit()
        return _redirect_back(f"/app/orders/{order_ref}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Collection failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/collect", methods=["POST"])
@login_required
def collect_sample(order_ref: str):
    try:
        biz.collect_sample(order_ref)
        biz.handover_sample(order_ref)
        db.session.commit()
        return _redirect_back(f"/app/orders/{order_ref}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Collect failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/receive", methods=["POST"])
@login_required
def receive_sample(order_ref: str):
    try:
        biz.receive_sample_at_lab(
            order_ref,
            received_by=request.form.get("received_by", "Lab tech"),
            accession_number=request.form.get("accession_number"),
        )
        db.session.commit()
        return _redirect_back(f"/app/orders/{order_ref}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Receive failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/enter-results", methods=["POST"])
@login_required
def enter_results(order_ref: str):
    try:
        order = biz.order_to_detail(order_ref)
        items = []
        for line in order.get("items", []):
            test_code = line["test_code"]
            items.append({
                "test_code": test_code,
                "test_name": line["test_name"],
                "result_value": request.form.get(f"result_{test_code}", "12.5"),
                "unit": request.form.get(f"unit_{test_code}", ""),
                "reference_range": request.form.get(f"ref_{test_code}", "10-15"),
            })
        if not items:
            items = [{"test_name": "Panel", "result_value": "12.5", "unit": "g/dL", "reference_range": "10-15"}]
        biz.enter_results(order_ref, items)
        db.session.commit()
        result = biz.order_to_detail(order_ref).get("result")
        code = result["result_code"] if result else order_ref
        return redirect(f"/app/reports/{code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Results failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/approve", methods=["POST"])
@login_required
def approve_result(order_ref: str):
    try:
        result = biz.approve_result(order_ref, doctor_note=request.form.get("doctor_note"))
        db.session.commit()
        return redirect(f"/app/reports/{result.result_code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Approval failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/orders/<order_ref>/release", methods=["POST"])
@login_required
def release_report(order_ref: str):
    try:
        result = biz.release_report(order_ref)
        db.session.commit()
        return redirect(f"/app/reports/{result.result_code}")
    except BusinessEngineError as exc:
        db.session.rollback()
        return _error_page("Release failed", str(exc), f"/app/orders/{order_ref}"), 400


@business_ui_bp.route("/app/business/reports/<result_code>/print", methods=["GET"])
@login_required
def print_report(result_code: str):
    try:
        detail = biz.result_to_detail(result_code)
        content = detail.get("html_content") or "<p>Report not released yet.</p>"
        return content, 200, {"Content-Type": "text/html; charset=utf-8"}
    except BusinessEngineError as exc:
        return _error_page("Report unavailable", str(exc), "/app/reports"), 404
