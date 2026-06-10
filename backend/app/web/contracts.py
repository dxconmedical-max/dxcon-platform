from flask import Blueprint

from app.models.contract import Contract
from app.models.company import Company


contracts_web_bp = Blueprint(
    "contracts_web",
    __name__
)


@contracts_web_bp.route("/contracts")
def contracts_page():

    contracts = Contract.query.all()

    rows = ""

    for contract in contracts:
        company = Company.query.get(contract.company_id)

        company_name = ""

        if company:
            company_name = company.company_name

        rows += f"""
        <tr>
            <td>{contract.contract_code}</td>
            <td>{company_name}</td>
            <td>{contract.title}</td>
            <td>{contract.contract_type}</td>
            <td>{contract.start_date}</td>
            <td>{contract.end_date}</td>
            <td><span class="status">{contract.status}</span></td>
            <td>{contract.total_value:,.0f} VND</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Contracts</title>
        <style>
            body {{
                margin: 0;
                font-family: Arial, sans-serif;
                background: #f1f5f9;
                color: #0f172a;
            }}

            .layout {{
                display: flex;
                min-height: 100vh;
            }}

            .sidebar {{
                width: 240px;
                background: #0a4b5c;
                color: white;
                padding: 24px;
            }}

            .sidebar h2 {{
                margin-top: 0;
                margin-bottom: 30px;
            }}

            .menu a {{
                display: block;
                color: white;
                text-decoration: none;
                padding: 12px 0;
                border-bottom: 1px solid rgba(255,255,255,.15);
            }}

            .content {{
                flex: 1;
                padding: 32px;
            }}

            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 24px;
            }}

            .btn {{
                background: #0d6efd;
                color: white;
                padding: 12px 18px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: bold;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0,0,0,.08);
            }}

            th {{
                background: #e2e8f0;
                text-align: left;
                padding: 14px;
                font-size: 13px;
            }}

            td {{
                padding: 14px;
                border-bottom: 1px solid #e5e7eb;
                font-size: 13px;
            }}

            .status {{
                background: #dcfce7;
                color: #166534;
                padding: 5px 10px;
                border-radius: 999px;
                font-weight: bold;
                font-size: 12px;
            }}
        </style>
    </head>

    <body>
        <div class="layout">

            <div class="sidebar">
                <h2>DxCon</h2>

                <div class="menu">
                    <a href="/dashboard">Dashboard</a>
                    <a href="/patients">Patients</a>
                    <a href="/companies">Companies</a>
                    <a href="/contracts">Contracts</a>
                    <a href="/orders">Orders</a>
                    <a href="/invoices">Invoices</a>
                    <a href="/payments">Payments</a>
                </div>
            </div>

            <div class="content">
                <div class="header">
                    <h1>Contracts Management</h1>
                    <a class="btn" href="#">+ New Contract</a>
                </div>

                <table>
                    <tr>
                        <th>Code</th>
                        <th>Company</th>
                        <th>Title</th>
                        <th>Type</th>
                        <th>Start Date</th>
                        <th>End Date</th>
                        <th>Status</th>
                        <th>Total Value</th>
                    </tr>

                    {rows}
                </table>
            </div>

        </div>
    </body>
    </html>
    """
