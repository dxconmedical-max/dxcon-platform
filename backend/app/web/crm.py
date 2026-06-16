from flask import Blueprint

from app.models.crm_lead import CrmLead
from app.utils.auth import role_required


crm_web_bp = Blueprint(
    "crm_web",
    __name__
)


@crm_web_bp.route("/crm")
@role_required("SUPER_ADMIN")
def crm_dashboard():

    leads = CrmLead.query.all()

    total_leads = len(leads)
    total_forecast = sum(lead.estimated_revenue or 0 for lead in leads)

    stages = ["LEAD", "CONTACTED", "MEETING", "PROPOSAL", "CONTRACT"]

    stage_counts = {}
    stage_revenue = {}

    for stage in stages:
        stage_counts[stage] = 0
        stage_revenue[stage] = 0

    for lead in leads:
        stage = lead.pipeline_stage or "LEAD"

        if stage not in stage_counts:
            stage_counts[stage] = 0
            stage_revenue[stage] = 0

        stage_counts[stage] += 1
        stage_revenue[stage] += lead.estimated_revenue or 0

    cards = ""

    for stage in stages:
        cards += f"""
        <div class="pipeline-card">
            <h3>{stage}</h3>
            <div class="big">{stage_counts.get(stage, 0)}</div>
            <p>{stage_revenue.get(stage, 0):,.0f} VND</p>
        """

        for lead in leads:
            if lead.pipeline_stage == stage:
                cards += f"""
                <div class="lead">
                    <b>{lead.company_name}</b><br>
                    {lead.contact_person or ""}<br>
                    <small>{lead.estimated_revenue or 0:,.0f} VND</small>
                </div>
                """

        cards += "</div>"

    lead_rows = ""

    for lead in leads:
        lead_rows += f"""
        <tr>
            <td>{lead.lead_code}</td>
            <td>{lead.company_name}</td>
            <td>{lead.contact_person or ""}</td>
            <td>{lead.phone or ""}</td>
            <td>{lead.email or ""}</td>
            <td>{lead.lead_source or ""}</td>
            <td>{lead.pipeline_stage}</td>
            <td>{lead.estimated_revenue:,.0f}</td>
            <td>{lead.owner or ""}</td>
        </tr>
        """

    contract_leads = stage_counts.get("CONTRACT", 0)
    conversion_rate = round(contract_leads / total_leads * 100, 1) if total_leads else 0

    return f"""
    <html>
    <head>
        <title>DxCon CRM & Sales Pipeline</title>
        <style>
            body {{
                font-family:Arial;
                background:#f1f5f9;
                padding:30px;
            }}
            .cards {{
                display:grid;
                grid-template-columns:repeat(4,1fr);
                gap:18px;
                margin-bottom:25px;
            }}
            .card {{
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
            .value {{
                font-size:30px;
                font-weight:bold;
                color:#0d6efd;
            }}
            .green {{ color:#198754; }}
            .purple {{ color:#7c3aed; }}
            .pipeline {{
                display:grid;
                grid-template-columns:repeat(5,1fr);
                gap:16px;
                margin-bottom:30px;
            }}
            .pipeline-card {{
                background:white;
                padding:18px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
                min-height:250px;
            }}
            .big {{
                font-size:34px;
                font-weight:bold;
                color:#0a4b5c;
            }}
            .lead {{
                background:#f8fafc;
                padding:10px;
                border-radius:8px;
                margin-top:10px;
                border-left:4px solid #0d6efd;
            }}
            table {{
                width:100%;
                border-collapse:collapse;
                background:white;
            }}
            th,td {{
                border:1px solid #cbd5e1;
                padding:10px;
                text-align:left;
            }}
            th {{
                background:#e2e8f0;
            }}
            .section {{
                background:white;
                padding:22px;
                border-radius:14px;
                box-shadow:0 4px 12px rgba(0,0,0,.08);
            }}
        </style>
    </head>

    <body>

        <h1>DxCon CRM & Sales Pipeline</h1>

        <div class="cards">
            <div class="card">
                <h3>Total Leads</h3>
                <div class="value">{total_leads}</div>
            </div>

            <div class="card">
                <h3>Revenue Forecast</h3>
                <div class="value green">{total_forecast:,.0f}</div>
            </div>

            <div class="card">
                <h3>Contract Leads</h3>
                <div class="value purple">{contract_leads}</div>
            </div>

            <div class="card">
                <h3>Conversion Rate</h3>
                <div class="value">{conversion_rate}%</div>
            </div>
        </div>

        <h2>Pipeline Board</h2>

        <div class="pipeline">
            {cards}
        </div>

        <div class="section">
            <h2>Lead List</h2>

            <table>
                <tr>
                    <th>Code</th>
                    <th>Company</th>
                    <th>Contact</th>
                    <th>Phone</th>
                    <th>Email</th>
                    <th>Source</th>
                    <th>Stage</th>
                    <th>Forecast</th>
                    <th>Owner</th>
                </tr>
                {lead_rows}
            </table>
        </div>

        <br>
        <a href="/dashboard">Dashboard</a>
        |
        <a href="/executive">CEO Dashboard</a>

    </body>
    </html>
    """
