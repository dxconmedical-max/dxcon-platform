from flask import Blueprint

from app.models.healthcare_standards import DICOMStudyMetadata, StandardCode, StandardMapping
from app.services.healthcare_standards_service import HealthcareStandardsService


healthcare_standards_web_bp = Blueprint("healthcare_standards_web", __name__)


def _styles():
    return """
    <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f4f6f8; color: #1f2933; }
    .layout { display: flex; min-height: 100vh; }
    .sidebar { width: 240px; background: #0b4f6c; color: #fff; padding: 20px; }
    .sidebar a { color: #bee9e8; display: block; margin: 8px 0; text-decoration: none; }
    .sidebar a.active { color: #fff; font-weight: bold; }
    .content { flex: 1; padding: 24px; }
    table { width: 100%; border-collapse: collapse; background: #fff; }
    th, td { border: 1px solid #d9e2ec; padding: 8px; text-align: left; }
    .card { background: #fff; padding: 16px; margin-bottom: 16px; border: 1px solid #d9e2ec; }
    </style>
    """


def _sidebar(active):
    links = [
        ("/standards", "Overview"),
        ("/standards/hl7", "HL7 v2"),
        ("/standards/fhir", "FHIR R4"),
        ("/standards/mappings", "Mappings"),
        ("/standards/dicom", "DICOM Metadata"),
    ]
    items = "".join(
        f'<a href="{href}" class="{"active" if href == active else ""}">{label}</a>' for href, label in links
    )
    return f'<div class="sidebar"><h2>Standards Gateway</h2>{items}</div>'


@healthcare_standards_web_bp.route("/standards")
def standards_home():
    systems = HealthcareStandardsService.list_code_systems()
    return f"""<!DOCTYPE html><html><head><title>Healthcare Standards</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/standards")}<div class="content">
    <h1>Healthcare Standards Gateway</h1>
    <div class="card"><strong>Supported code systems:</strong> {systems["count"]}<br>
    HL7 v2, FHIR R4, LOINC, ICD-10, SNOMED CT, DICOM metadata</div>
    </div></div></body></html>"""


@healthcare_standards_web_bp.route("/standards/hl7")
def standards_hl7():
    return f"""<!DOCTYPE html><html><head><title>HL7 v2</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/standards/hl7")}<div class="content">
    <h1>HL7 v2 Foundation</h1>
    <div class="card">Supported message types: ADT, ORM, ORU<br>
    API: <code>POST /api/v1/standards/hl7/parse</code>, <code>/validate</code>, <code>/build-oru</code></div>
    </div></div></body></html>"""


@healthcare_standards_web_bp.route("/standards/fhir")
def standards_fhir():
    return f"""<!DOCTYPE html><html><head><title>FHIR R4</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/standards/fhir")}<div class="content">
    <h1>FHIR R4 Foundation</h1>
    <div class="card">Supported resources: Patient, Practitioner, Organization, ServiceRequest, Specimen, Observation, DiagnosticReport</div>
    </div></div></body></html>"""


@healthcare_standards_web_bp.route("/standards/mappings")
def standards_mappings():
    rows = StandardMapping.query.limit(20).all()
    table = "".join(
        f"<tr><td>{row.source_type}</td><td>{row.source_code}</td><td>{row.target_system}</td><td>{row.target_code}</td></tr>"
        for row in rows
    )
    return f"""<!DOCTYPE html><html><head><title>Mappings</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/standards/mappings")}<div class="content">
    <h1>Clinical Code Mapping</h1>
    <table><tr><th>Source Type</th><th>Source Code</th><th>Target System</th><th>Target Code</th></tr>
    {table or "<tr><td colspan='4'>No mappings</td></tr>"}</table>
    </div></div></body></html>"""


@healthcare_standards_web_bp.route("/standards/dicom")
def standards_dicom():
    count = DICOMStudyMetadata.query.count()
    codes = StandardCode.query.count()
    return f"""<!DOCTYPE html><html><head><title>DICOM</title>{_styles()}</head><body>
    <div class="layout">{_sidebar("/standards/dicom")}<div class="content">
    <h1>DICOM Metadata Foundation</h1>
    <div class="card">Studies indexed: {count}<br>Standard codes loaded: {codes}<br>No image storage or viewer implemented.</div>
    </div></div></body></html>"""
