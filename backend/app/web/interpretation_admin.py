from flask import Blueprint

from app.services.interpretation_engine_service import (
    CriticalValueService,
    InterpretationEngine,
    ReferenceRangeService,
)


interpretation_admin_web_bp = Blueprint("interpretation_admin_web", __name__)


def _styles():
    return """
    body { margin:0; font-family:Arial,sans-serif; background:#f8fafc; color:#0f172a; }
    .layout { max-width:1100px; margin:0 auto; padding:32px; }
    .nav a { margin-right:16px; }
    .card { background:white; border-radius:12px; padding:24px; box-shadow:0 4px 12px rgba(0,0,0,.08); margin-bottom:24px; }
    table { width:100%; border-collapse:collapse; }
    th, td { padding:12px; border-bottom:1px solid #e5e7eb; text-align:left; font-size:14px; }
    th { background:#e2e8f0; }
    """


def _nav(active):
    links = [
        ("/interpretation", "Interpretation"),
        ("/reference-ranges", "Reference Ranges"),
        ("/critical-values", "Critical Values"),
    ]
    items = ""
    for href, label in links:
        style = ' style="font-weight:bold;"' if href == active else ""
        items += f'<a href="{href}"{style}>{label}</a>'
    return f'<div class="nav">{items}</div>'


@interpretation_admin_web_bp.route("/interpretation")
def interpretation_home():
    rules = InterpretationEngine.list_rules()
    templates = InterpretationEngine.list_templates()
    rule_rows = ""
    for rule in rules:
        rule_rows += f"""
        <tr>
            <td>{rule.rule_code}</td>
            <td>{rule.test_code or ""}</td>
            <td>{rule.condition_flag}</td>
            <td>{rule.risk_level}</td>
            <td>{rule.finding_en or ""}</td>
        </tr>
        """
    template_rows = ""
    for template in templates:
        template_rows += f"""
        <tr>
            <td>{template.template_code}</td>
            <td>v{template.version}</td>
            <td>{template.language}</td>
            <td>{template.title or ""}</td>
        </tr>
        """

    return f"""
    <html><head><title>Interpretation Engine</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card"><h1>AI Interpretation Engine</h1>{_nav("/interpretation")}</div>
    <div class="card"><h2>Interpretation Rules</h2>
    <table><tr><th>Code</th><th>Test</th><th>Flag</th><th>Risk</th><th>Finding</th></tr>{rule_rows or "<tr><td colspan='5'>No rules</td></tr>"}</table>
    </div>
    <div class="card"><h2>Templates</h2>
    <table><tr><th>Code</th><th>Version</th><th>Language</th><th>Title</th></tr>{template_rows or "<tr><td colspan='4'>No templates</td></tr>"}</table>
    </div>
    </div></body></html>
    """


@interpretation_admin_web_bp.route("/reference-ranges")
def reference_ranges_home():
    ranges = ReferenceRangeService.list_ranges()
    rows = ""
    for row in ranges:
        rows += f"""
        <tr>
            <td>{row.test_code}</td>
            <td>{row.test_name or ""}</td>
            <td>{row.sex}</td>
            <td>{row.age_min}-{row.age_max}</td>
            <td>{row.low_value}-{row.high_value}</td>
            <td>{row.unit or ""}</td>
        </tr>
        """

    return f"""
    <html><head><title>Reference Ranges</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card"><h1>Reference Ranges</h1>{_nav("/reference-ranges")}</div>
    <div class="card">
    <table><tr><th>Code</th><th>Test</th><th>Sex</th><th>Age</th><th>Range</th><th>Unit</th></tr>{rows or "<tr><td colspan='6'>No ranges</td></tr>"}</table>
    </div>
    </div></body></html>
    """


@interpretation_admin_web_bp.route("/critical-values")
def critical_values_home():
    rules = CriticalValueService.list_rules()
    rows = ""
    for rule in rules:
        rows += f"""
        <tr>
            <td>{rule.rule_code}</td>
            <td>{rule.test_code}</td>
            <td>{rule.panic_low if rule.panic_low is not None else ""}</td>
            <td>{rule.panic_high if rule.panic_high is not None else ""}</td>
            <td>{rule.severity}</td>
            <td>{rule.message_en or ""}</td>
        </tr>
        """

    return f"""
    <html><head><title>Critical Values</title><style>{_styles()}</style></head><body>
    <div class="layout">
    <div class="card"><h1>Critical Value Rules</h1>{_nav("/critical-values")}</div>
    <div class="card">
    <table><tr><th>Code</th><th>Test</th><th>Panic Low</th><th>Panic High</th><th>Severity</th><th>Message</th></tr>{rows or "<tr><td colspan='6'>No rules</td></tr>"}</table>
    </div>
    </div></body></html>
    """
