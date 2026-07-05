"""Master Data Management dashboard UI."""

from __future__ import annotations

import html

from flask import Blueprint, render_template_string

from app.mdm.registry import ENTITY_LABELS, ENTITY_TYPES
from app.mdm.service import dashboard_stats

mdm_web_bp = Blueprint("mdm_web", __name__)

_STYLES = """
body { font-family: system-ui, sans-serif; margin: 0; background: #f1f5f9; color: #0f172a; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 24px; }
.card { background: #fff; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,.06); }
h1 { margin: 0 0 8px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }
.metric { background: #e0f2fe; border-radius: 10px; padding: 14px; }
.metric strong { display: block; font-size: 22px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { padding: 10px; border-bottom: 1px solid #e2e8f0; text-align: left; }
th { background: #f8fafc; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; background: #dbeafe; }
a { color: #0369a1; }
"""


def _esc(value) -> str:
    return html.escape(str(value))


@mdm_web_bp.route("/app/mdm")
def mdm_dashboard():
    stats = dashboard_stats()
    totals = stats["totals"]
    entity_rows = ""
    for item in stats["counts_by_entity"]:
        entity_rows += (
            f"<tr><td>{_esc(item['label'])}</td><td><code>{_esc(item['entity_type'])}</code></td>"
            f"<td>{item['count']}</td></tr>"
        )
    missing = ", ".join(_esc(e) for e in stats["missing_data"]) or "—"
    dup_rows = ""
    for dup in stats["duplicate_records"][:10]:
        dup_rows += f"<tr><td>{_esc(dup['entity_type'])}</td><td><code>{_esc(dup['code'])}</code></td><td>{dup['count']}</td></tr>"
    import_rows = ""
    for batch in stats["import_history"][:10]:
        import_rows += (
            f"<tr><td>{_esc(batch['batch_code'])}</td><td>{_esc(batch['entity_type'])}</td>"
            f"<td><span class='badge'>{_esc(batch['status'])}</span></td>"
            f"<td>{batch.get('committed_rows', 0)}/{batch.get('total_rows', 0)}</td></tr>"
        )
    modules = " · ".join(_esc(ENTITY_LABELS.get(e, e)) for e in ENTITY_TYPES)

    body = f"""
    <div class="wrap">
      <div class="card">
        <h1>Master Data Management</h1>
        <p>Single source of truth for DxCon platform master data.</p>
        <p><a href="/api/v1/mdm/dashboard">JSON dashboard</a> · <a href="/api/v1/mdm/report">Master data report</a></p>
      </div>
      <div class="card grid">
        <div class="metric"><span>Total records</span><strong>{totals['records']}</strong></div>
        <div class="metric"><span>Active</span><strong>{totals['active']}</strong></div>
        <div class="metric"><span>Inactive</span><strong>{totals['inactive']}</strong></div>
        <div class="metric"><span>Entity types</span><strong>{totals['populated_entity_types']}/{totals['entity_types']}</strong></div>
      </div>
      <div class="card">
        <h2>Entity coverage</h2>
        <table><tr><th>Module</th><th>Type</th><th>Records</th></tr>{entity_rows}</table>
      </div>
      <div class="card">
        <h2>Missing data</h2>
        <p>{missing}</p>
        <h3>Modules ({len(ENTITY_TYPES)})</h3>
        <p style="font-size:13px;line-height:1.6">{modules}</p>
      </div>
      <div class="card">
        <h2>Duplicate records</h2>
        <table><tr><th>Entity</th><th>Code</th><th>Count</th></tr>{dup_rows or "<tr><td colspan='3'>None detected</td></tr>"}</table>
      </div>
      <div class="card">
        <h2>Import templates</h2>
        <p>CSV and Excel templates for all 18 modules live under <code>backend/templates/mdm/</code>.</p>
        <p>Download schema: <code>GET /api/v1/mdm/imports/&lt;entity_type&gt;/template</code></p>
      </div>
      <div class="card">
        <h2>Import history</h2>
        <table><tr><th>Batch</th><th>Entity</th><th>Status</th><th>Committed</th></tr>{import_rows or "<tr><td colspan='4'>No imports yet</td></tr>"}</table>
        <p style="margin-top:12px">Upload via <code>POST /api/v1/mdm/imports/&lt;entity_type&gt;</code> (CSV or Excel).</p>
      </div>
    </div>
    """
    return render_template_string(f"<html><head><title>MDM Dashboard</title><style>{_STYLES}</style></head><body>{body}</body></html>")
