from flask import Blueprint

from app.models.company import Company


companies_web_bp = Blueprint(
    "companies_web",
    __name__
)


@companies_web_bp.route("/companies")
def companies_page():

    companies = Company.query.all()

    rows = ""

    for company in companies:
        rows += f"""
        <tr>
            <td>{company.company_code}</td>
            <td>{company.company_name}</td>
            <td>{company.tax_code or ""}</td>
            <td>{company.contact_person or ""}</td>
            <td>{company.phone or ""}</td>
            <td>{company.status}</td>
        </tr>
        """

    return f"""
    <html>
    <head>
        <title>DxCon Companies</title>
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
            }}

            td {{
                padding: 14px;
                border-bottom: 1px solid #e5e7eb;
            }}

            .status {{
                font-weight: bold;
                color: #198754;
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
                    <h1>Companies Management</h1>
                    <a class="btn" href="#">+ New Company</a>
                </div>

                <table>
                    <tr>
                        <th>Code</th>
                        <th>Company Name</th>
                        <th>Tax Code</th>
                        <th>Contact Person</th>
                        <th>Phone</th>
                        <th>Status</th>
                    </tr>

                    {rows}
                </table>
            </div>

        </div>
    </body>
    </html>
    """
