from flask import Blueprint

from app.models.user import User

from app.core.web_authz import web_roles_required

@security_web_bp.route("/security")
@web_roles_required("SUPER_ADMIN")
security_web_bp = Blueprint("security_web", __name__)


@security_web_bp.route("/security")
def security_dashboard():

    users = User.query.all()

    rows = ""

    for u in users:
        rows += f"""
        <tr>
            <td>{u.email}</td>
            <td>{u.phone or ""}</td>
            <td>{u.role}</td>
            <td>{u.is_active}</td>
            <td>{u.created_at}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:30px;">
        <h1>DxCon Security Center</h1>

        <div style="background:white;padding:20px;border-radius:12px;">
            <h2>Users & Roles</h2>

            <table border="1" cellpadding="10" style="width:100%;border-collapse:collapse;">
                <tr>
                    <th>Email</th>
                    <th>Phone</th>
                    <th>Role</th>
                    <th>Active</th>
                    <th>Created</th>
                </tr>
                {rows}
            </table>
        </div>

        <br>
        <a href="/executive-v9">Executive</a> |
        <a href="/finance">Finance</a> |
        <a href="/crm-pipeline">CRM</a>
    </body>
    </html>
    """
