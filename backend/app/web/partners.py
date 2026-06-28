from flask import Blueprint, redirect, request

from app.core.statuses import VALID_PARTNER_API_STATUSES, VALID_PARTNER_TYPES
from app.services.partner_platform import PartnerPlatformError, PartnerPlatformService


partners_web_bp = Blueprint(
    "partners_web",
    __name__,
)


def _sidebar_html():
    return """
    <div class="sidebar">
        <h2>DxCon</h2>
        <div class="menu">
            <a href="/dashboard">Dashboard</a>
            <a href="/patients">Patients</a>
            <a href="/companies">Companies</a>
            <a href="/partners">Partners</a>
            <a href="/contracts">Contracts</a>
            <a href="/orders">Orders</a>
            <a href="/invoices">Invoices</a>
            <a href="/payments">Payments</a>
        </div>
    </div>
    """


def _page_styles():
    return """
    body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #f1f5f9;
        color: #0f172a;
    }
    .layout { display: flex; min-height: 100vh; }
    .sidebar {
        width: 240px;
        background: #0a4b5c;
        color: white;
        padding: 24px;
    }
    .sidebar h2 { margin-top: 0; margin-bottom: 30px; }
    .menu a {
        display: block;
        color: white;
        text-decoration: none;
        padding: 12px 0;
        border-bottom: 1px solid rgba(255,255,255,.15);
    }
    .content { flex: 1; padding: 32px; }
    .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
    }
    .btn {
        background: #0d6efd;
        color: white;
        padding: 12px 18px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        border: none;
        cursor: pointer;
        display: inline-block;
    }
    .btn-success { background: #198754; }
    .btn-danger { background: #dc3545; }
    .btn-secondary { background: #6c757d; }
    table {
        width: 100%;
        border-collapse: collapse;
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
        margin-bottom: 24px;
    }
    th { background: #e2e8f0; text-align: left; padding: 14px; }
    td { padding: 14px; border-bottom: 1px solid #e5e7eb; }
    .card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 12px rgba(0,0,0,.08);
        margin-bottom: 24px;
    }
    .field { margin-bottom: 16px; }
    .field label { display: block; font-weight: bold; margin-bottom: 6px; }
    .field input, .field select, .field textarea {
        width: 100%;
        padding: 10px;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        box-sizing: border-box;
    }
    .status-pending { color: #ca8a04; font-weight: bold; }
    .status-draft { color: #64748b; font-weight: bold; }
    .status-submitted { color: #2563eb; font-weight: bold; }
    .status-under-review { color: #7c3aed; font-weight: bold; }
    .status-approved { color: #198754; font-weight: bold; }
    .status-active { color: #059669; font-weight: bold; }
    .status-rejected { color: #dc3545; font-weight: bold; }
    .status-suspended { color: #6c757d; font-weight: bold; }
    .status-archived { color: #475569; font-weight: bold; }
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 16px;
        margin: 16px 0;
    }
    .metric {
        background: #f8fafc;
        border-radius: 8px;
        padding: 14px;
        border: 1px solid #e2e8f0;
    }
    .metric-label { font-size: 12px; color: #64748b; text-transform: uppercase; }
    .metric-value { font-size: 22px; font-weight: bold; margin-top: 6px; }
    .actions { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
    """


def _status_class(status):
    normalized = status.lower().replace("_", "-")
    return f"status-{normalized}"


@partners_web_bp.route("/partners")
def partners_page():
    partners = PartnerPlatformService.list_partners()

    rows = ""
    for partner in partners:
        rows += f"""
        <tr>
            <td><a href="/partners/{partner.id}">{partner.partner_code}</a></td>
            <td>{partner.partner_type}</td>
            <td>{partner.display_name}</td>
            <td>{partner.city or ""}</td>
            <td class="{_status_class(partner.status)}">{partner.status}</td>
            <td>{partner.api_status}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Partners</title>
        <style>{_page_styles()}</style>
    </head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Partner Platform</h1>
                    <a class="btn" href="/partners/new">+ New Partner</a>
                </div>
                <table>
                    <tr>
                        <th>Code</th>
                        <th>Type</th>
                        <th>Display Name</th>
                        <th>City</th>
                        <th>Status</th>
                        <th>API Status</th>
                    </tr>
                    {rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@partners_web_bp.route("/partners/new", methods=["GET", "POST"])
def partners_new_page():
    error = ""

    if request.method == "POST":
        data = {
            "partner_type": request.form.get("partner_type"),
            "legal_name": request.form.get("legal_name"),
            "display_name": request.form.get("display_name"),
            "tax_code": request.form.get("tax_code"),
            "license_number": request.form.get("license_number"),
            "representative_name": request.form.get("representative_name"),
            "phone": request.form.get("phone"),
            "email": request.form.get("email"),
            "address": request.form.get("address"),
            "city": request.form.get("city"),
            "district": request.form.get("district"),
            "api_status": request.form.get("api_status", "OFFLINE"),
        }

        try:
            partner = PartnerPlatformService.create_partner(data)
            return redirect(f"/partners/{partner.id}")
        except PartnerPlatformError as exc:
            error = exc.message

    type_options = "".join(
        f'<option value="{item}">{item}</option>'
        for item in VALID_PARTNER_TYPES
    )
    api_options = "".join(
        f'<option value="{item}">{item}</option>'
        for item in VALID_PARTNER_API_STATUSES
    )

    return f"""
    <html>
    <head>
        <title>New Partner - DxCon</title>
        <style>{_page_styles()}</style>
    </head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>Register New Partner</h1>
                    <a class="btn btn-secondary" href="/partners">Back to List</a>
                </div>
                {"<p style='color:#dc3545;font-weight:bold;'>" + error + "</p>" if error else ""}
                <div class="card">
                    <form method="POST">
                        <div class="field">
                            <label>Partner Type</label>
                            <select name="partner_type" required>{type_options}</select>
                        </div>
                        <div class="field">
                            <label>Legal Name</label>
                            <input name="legal_name" required />
                        </div>
                        <div class="field">
                            <label>Display Name</label>
                            <input name="display_name" required />
                        </div>
                        <div class="field">
                            <label>Tax Code</label>
                            <input name="tax_code" />
                        </div>
                        <div class="field">
                            <label>License Number</label>
                            <input name="license_number" />
                        </div>
                        <div class="field">
                            <label>Representative Name</label>
                            <input name="representative_name" />
                        </div>
                        <div class="field">
                            <label>Phone</label>
                            <input name="phone" />
                        </div>
                        <div class="field">
                            <label>Email</label>
                            <input name="email" type="email" />
                        </div>
                        <div class="field">
                            <label>Address</label>
                            <textarea name="address" rows="3"></textarea>
                        </div>
                        <div class="field">
                            <label>City</label>
                            <input name="city" />
                        </div>
                        <div class="field">
                            <label>District</label>
                            <input name="district" />
                        </div>
                        <div class="field">
                            <label>API Status</label>
                            <select name="api_status">{api_options}</select>
                        </div>
                        <button class="btn" type="submit">Create Partner</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


@partners_web_bp.route("/partners/<partner_id>")
def partner_detail_page(partner_id):
    try:
        partner = PartnerPlatformService.get_partner(partner_id)
        services = PartnerPlatformService.list_partner_services(partner_id)
        verification_items = PartnerPlatformService.list_verification_items(partner_id)
        credentials = PartnerPlatformService.list_api_credentials(partner_id)
    except PartnerPlatformError:
        return "<h1>Partner not found</h1>", 404

    service_rows = ""
    for service in services:
        sla_hours = service.average_result_time_hours or partner.average_result_time_hours or ""
        service_rows += f"""
        <tr>
            <td>{service.service_code}</td>
            <td>{service.service_name}</td>
            <td>{service.catalog_item_code or ""}</td>
            <td>{sla_hours}</td>
            <td>{service.status}</td>
        </tr>
        """

    verification_rows = ""
    for item in verification_items:
        verification_rows += f"""
        <tr>
            <td>{item.item_type}</td>
            <td>{item.status}</td>
            <td>{item.note or ""}</td>
            <td>{item.verified_by or ""}</td>
            <td>{item.verified_at.strftime("%Y-%m-%d %H:%M") if item.verified_at else ""}</td>
        </tr>
        """

    credential_rows = ""
    for credential in credentials:
        credential_rows += f"""
        <tr>
            <td>{credential.client_id}</td>
            <td>{credential.status}</td>
            <td>{credential.created_at.strftime("%Y-%m-%d %H:%M") if credential.created_at else ""}</td>
            <td>{credential.revoked_at.strftime("%Y-%m-%d %H:%M") if credential.revoked_at else ""}</td>
        </tr>
        """

    workflow_actions = []
    if partner.status in ("DRAFT", "PENDING"):
        workflow_actions.append(
            f'<a class="btn" href="/partners/{partner.id}/submit">Submit</a>'
        )
    if partner.status in ("SUBMITTED", "PENDING"):
        workflow_actions.append(
            f'<a class="btn" href="/partners/{partner.id}/review">Start Review</a>'
        )
    if partner.status in ("PENDING", "SUBMITTED", "UNDER_REVIEW"):
        workflow_actions.append(
            f'<a class="btn btn-success" href="/partners/{partner.id}/approve">Approve</a>'
        )
        workflow_actions.append(
            f'<a class="btn btn-danger" href="/partners/{partner.id}/reject">Reject</a>'
        )
    if partner.status == "APPROVED":
        workflow_actions.append(
            f'<a class="btn btn-success" href="/partners/{partner.id}/activate">Activate</a>'
        )
    if partner.status in ("ACTIVE", "APPROVED"):
        workflow_actions.append(
            f'<a class="btn btn-danger" href="/partners/{partner.id}/suspend">Suspend</a>'
        )
    if partner.status not in ("ARCHIVED",):
        workflow_actions.append(
            f'<a class="btn btn-secondary" href="/partners/{partner.id}/archive">Archive</a>'
        )
    workflow_actions.append(
        f'<a class="btn btn-secondary" href="/partners/{partner.id}/credentials/create">Create API Credential</a>'
    )

    workflow_html = ""
    if workflow_actions:
        workflow_html = f'<div class="actions">{"".join(workflow_actions)}</div>'

    rating_value = partner.rating if partner.rating is not None else 0
    review_count = partner.review_count or 0
    completed_orders = partner.completed_orders or 0

    return f"""
    <html>
    <head>
        <title>{partner.display_name} - DxCon</title>
        <style>{_page_styles()}</style>
    </head>
    <body>
        <div class="layout">
            {_sidebar_html()}
            <div class="content">
                <div class="header">
                    <h1>{partner.display_name}</h1>
                    <a class="btn btn-secondary" href="/partners">Back to List</a>
                </div>
                <div class="card">
                    <p><strong>Code:</strong> {partner.partner_code}</p>
                    <p><strong>Type:</strong> {partner.partner_type}</p>
                    <p><strong>Legal Name:</strong> {partner.legal_name}</p>
                    <p><strong>Status:</strong> <span class="{_status_class(partner.status)}">{partner.status}</span></p>
                    <p><strong>API Status:</strong> {partner.api_status}</p>
                    <div class="metric-grid">
                        <div class="metric">
                            <div class="metric-label">Rating</div>
                            <div class="metric-value">{rating_value:.1f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Reviews</div>
                            <div class="metric-value">{review_count}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Completed Orders</div>
                            <div class="metric-value">{completed_orders}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Result SLA (hrs)</div>
                            <div class="metric-value">{partner.average_result_time_hours or "-"}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Pickup SLA (min)</div>
                            <div class="metric-value">{partner.pickup_sla_minutes or "-"}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Response SLA (min)</div>
                            <div class="metric-value">{partner.response_sla_minutes or "-"}</div>
                        </div>
                    </div>
                    <p><strong>Working Hours:</strong> {partner.working_hours_summary or ""}</p>
                    <p><strong>Tax Code:</strong> {partner.tax_code or ""}</p>
                    <p><strong>License:</strong> {partner.license_number or ""}</p>
                    <p><strong>Representative:</strong> {partner.representative_name or ""}</p>
                    <p><strong>Phone:</strong> {partner.phone or ""}</p>
                    <p><strong>Email:</strong> {partner.email or ""}</p>
                    <p><strong>Address:</strong> {partner.address or ""}</p>
                    <p><strong>City / District:</strong> {partner.city or ""} / {partner.district or ""}</p>
                    <p><strong>Verification Note:</strong> {partner.verification_note or ""}</p>
                    {workflow_html}
                </div>
                <h2>Verification Checklist</h2>
                <table>
                    <tr>
                        <th>Item</th>
                        <th>Status</th>
                        <th>Note</th>
                        <th>Verified By</th>
                        <th>Verified At</th>
                    </tr>
                    {verification_rows}
                </table>
                <h2>API Credentials</h2>
                <table>
                    <tr>
                        <th>Client ID</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Revoked</th>
                    </tr>
                    {credential_rows}
                </table>
                <h2>Services</h2>
                <div class="card">
                    <form method="POST" action="/partners/{partner.id}/services">
                        <div class="field">
                            <label>Service Code</label>
                            <input name="service_code" required />
                        </div>
                        <div class="field">
                            <label>Service Name</label>
                            <input name="service_name" required />
                        </div>
                        <div class="field">
                            <label>Catalog Item Code</label>
                            <input name="catalog_item_code" />
                        </div>
                        <div class="field">
                            <label>Description</label>
                            <textarea name="description" rows="2"></textarea>
                        </div>
                        <button class="btn" type="submit">Add Service</button>
                    </form>
                </div>
                <table>
                    <tr>
                        <th>Code</th>
                        <th>Name</th>
                        <th>Catalog Item</th>
                        <th>Result SLA (hrs)</th>
                        <th>Status</th>
                    </tr>
                    {service_rows}
                </table>
            </div>
        </div>
    </body>
    </html>
    """


@partners_web_bp.route("/partners/<partner_id>/approve")
def partner_approve_page(partner_id):
    try:
        PartnerPlatformService.approve_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/reject")
def partner_reject_page(partner_id):
    try:
        PartnerPlatformService.reject_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/submit")
def partner_submit_page(partner_id):
    try:
        PartnerPlatformService.submit_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/review")
def partner_review_page(partner_id):
    try:
        PartnerPlatformService.start_review(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/activate")
def partner_activate_page(partner_id):
    try:
        PartnerPlatformService.activate_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/suspend")
def partner_suspend_page(partner_id):
    try:
        PartnerPlatformService.suspend_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/archive")
def partner_archive_page(partner_id):
    try:
        PartnerPlatformService.archive_partner(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/credentials/create")
def partner_create_credential_page(partner_id):
    try:
        PartnerPlatformService.create_api_credential(partner_id)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")


@partners_web_bp.route("/partners/<partner_id>/services", methods=["POST"])
def partner_add_service_page(partner_id):
    data = {
        "service_code": request.form.get("service_code"),
        "service_name": request.form.get("service_name"),
        "catalog_item_code": request.form.get("catalog_item_code"),
        "description": request.form.get("description"),
    }

    try:
        PartnerPlatformService.add_partner_service(partner_id, data)
    except PartnerPlatformError:
        pass

    return redirect(f"/partners/{partner_id}")
