from flask import Blueprint

home_web_bp = Blueprint("home_web", __name__)


@home_web_bp.route("/")
def index():
    return """
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Platform</h1>
        <p>Production API is running.</p>

        <ul>
            <li><a href="/executive-v9">Executive V9</a></li>
            <li><a href="/finance">Finance</a></li>
            <li><a href="/crm-pipeline">CRM Pipeline</a></li>
            <li><a href="/logistics">Logistics</a></li>
            <li><a href="/collector">Collector</a></li>
            <li><a href="/doctor-workbench">Doctor Workbench</a></li>
            <li><a href="/api/v1/workflow/health">Workflow Health</a></li>
        </ul>
    </body>
    </html>
    """
