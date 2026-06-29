from flask import Blueprint, redirect, request

from app.models.medical_order import MedicalOrder
from app.services.result_gateway_service import ResultGatewayBase, ResultUploadService


result_gateway_web_bp = Blueprint("result_gateway_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { max-width:1100px; margin:0 auto; padding:32px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    .btn { background:#0d6efd; color:white; padding:10px 16px; border-radius:8px; text-decoration:none; display:inline-block; border:0; cursor:pointer; }
    .badge { padding:4px 8px; border-radius:999px; background:#dbeafe; font-size:12px; }
    input, textarea, select { width:100%; padding:10px; margin:8px 0 16px; border:1px solid #cbd5e1; border-radius:8px; }
    """


@result_gateway_web_bp.route("/results/new")
def legacy_results_new_redirect():
    return redirect("/results/upload")


@result_gateway_web_bp.route("/results")
def results_home():
    results = ResultGatewayBase.list_results()
    rows = ""
    for result in results:
        rows += f"""
        <tr>
            <td><a href="/results/{result.id}">{result.result_code}</a></td>
            <td>{result.patient_name or ""}</td>
            <td>{result.source_type}</td>
            <td><span class="badge">{result.status}</span></td>
            <td>{result.created_at}</td>
        </tr>
        """

    return f"""
    <html><head><title>Result Gateway</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card">
        <h1>Result Gateway</h1>
        <a class="btn" href="/results/upload">Upload Result</a>
    </div>
    <div class="card">
        <table>
            <tr><th>Code</th><th>Patient</th><th>Source</th><th>Status</th><th>Created</th></tr>
            {rows or "<tr><td colspan='5'>No results yet</td></tr>"}
        </table>
    </div>
    </div></body></html>
    """


@result_gateway_web_bp.route("/results/upload", methods=["GET", "POST"])
def results_upload():
    orders = MedicalOrder.query.order_by(MedicalOrder.created_at.desc()).limit(20).all()
    order_options = "".join(
        f'<option value="{order.id}">{order.order_code} - {order.patient_name}</option>'
        for order in orders
    )

    message = ""
    if request.method == "POST":
        order_id = request.form.get("medical_order_id")
        try:
            ResultUploadService.create_manual(
                {
                    "medical_order_id": order_id,
                    "summary": request.form.get("summary"),
                    "items": [
                        {
                            "test_code": request.form.get("test_code"),
                            "test_name": request.form.get("test_name"),
                            "result_value": request.form.get("result_value"),
                            "unit": request.form.get("unit"),
                            "reference_range": request.form.get("reference_range"),
                        }
                    ],
                    "attachments": [
                        {
                            "file_name": request.form.get("file_name"),
                            "file_path": request.form.get("file_path"),
                            "mime_type": request.form.get("mime_type"),
                        }
                    ]
                    if request.form.get("file_name")
                    else [],
                },
                actor_email="WEB",
            )
            message = "Result uploaded successfully"
        except Exception as exc:
            message = getattr(exc, "message", str(exc))

    return f"""
    <html><head><title>Upload Result</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card">
        <h1>Upload / Manual Entry</h1>
        <p>{message}</p>
        <form method="POST">
            <label>Medical Order</label>
            <select name="medical_order_id">{order_options}</select>
            <label>Summary</label>
            <textarea name="summary" placeholder="Optional summary"></textarea>
            <label>Test Code</label>
            <input name="test_code" placeholder="GLU">
            <label>Test Name</label>
            <input name="test_name" placeholder="Glucose" required>
            <label>Result Value</label>
            <input name="result_value" placeholder="5.4" required>
            <label>Unit</label>
            <input name="unit" placeholder="mmol/L">
            <label>Reference Range</label>
            <input name="reference_range" placeholder="3.9-6.1">
            <label>Attachment File Name</label>
            <input name="file_name" placeholder="result.pdf">
            <label>Attachment Path</label>
            <input name="file_path" placeholder="/uploads/results/result.pdf">
            <label>MIME Type</label>
            <input name="mime_type" placeholder="application/pdf">
            <button class="btn" type="submit">Save Result</button>
        </form>
        <br><a href="/results">Back to Results</a>
    </div>
    </div></body></html>
    """


@result_gateway_web_bp.route("/results/<result_id>")
def results_detail(result_id):
    try:
        result = ResultGatewayBase.get_result_detail(result_id)
    except Exception:
        return "Result not found", 404

    item_rows = ""
    for item in result.get("items", []):
        item_rows += f"""
        <tr>
            <td>{item.get("test_code", "")}</td>
            <td>{item.get("test_name", "")}</td>
            <td>{item.get("result_value", "")}</td>
            <td>{item.get("unit", "")}</td>
            <td>{item.get("reference_range", "")}</td>
            <td>{item.get("flag", "")}</td>
        </tr>
        """

    attachment_rows = ""
    for attachment in result.get("attachments", []):
        attachment_rows += f"""
        <tr>
            <td>{attachment.get("file_name", "")}</td>
            <td>{attachment.get("attachment_type", "")}</td>
            <td>{attachment.get("file_path", "")}</td>
        </tr>
        """

    timeline_rows = ""
    for entry in ResultGatewayBase.get_timeline(result_id):
        timeline_rows += f"""
        <tr>
            <td>{entry.event_type}</td>
            <td>{entry.from_status or ""} -> {entry.to_status or ""}</td>
            <td>{entry.message or ""}</td>
            <td>{entry.actor_email}</td>
            <td>{entry.created_at}</td>
        </tr>
        """

    release = result.get("release")
    release_block = ""
    if release:
        release_block = f"""
        <div class="card">
            <h2>Released Version v{release.get("version")}</h2>
            <p>Release code: {release.get("release_code")}</p>
            <p>Released at: {release.get("released_at")}</p>
        </div>
        """

    return f"""
    <html><head><title>{result.get("result_code")}</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card">
        <h1>{result.get("result_code")}</h1>
        <p>Patient: {result.get("patient_name", "")} | Status: <span class="badge">{result.get("status")}</span></p>
        <p>Source: {result.get("source_type")} | Locked: {result.get("is_locked")}</p>
        <a href="/results">Back to Results</a>
    </div>
    <div class="card"><h2>Items</h2>
    <table><tr><th>Code</th><th>Test</th><th>Value</th><th>Unit</th><th>Ref</th><th>Flag</th></tr>{item_rows}</table>
    </div>
    <div class="card"><h2>Attachments</h2>
    <table><tr><th>File</th><th>Type</th><th>Path</th></tr>{attachment_rows or "<tr><td colspan='3'>None</td></tr>"}</table>
    </div>
    {release_block}
    <div class="card"><h2>Timeline</h2>
    <table><tr><th>Event</th><th>Status</th><th>Message</th><th>Actor</th><th>At</th></tr>{timeline_rows}</table>
    </div>
    </div></body></html>
    """
