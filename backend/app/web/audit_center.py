from flask import Blueprint
from app.models.audit_log import AuditLog

audit_center_web_bp = Blueprint(
    "audit_center_web",
    __name__
)


@audit_center_web_bp.route("/audit")
def audit_center():

    logs = AuditLog.query.order_by(
        AuditLog.created_at.desc()
    ).limit(200).all()

    rows = ""

    for log in logs:
        rows += f"""
        <tr>
            <td>{log.created_at}</td>
            <td>{log.user_email or ""}</td>
            <td>{log.action or ""}</td>
            <td>{log.object_type or ""}</td>
            <td>{log.object_id or ""}</td>
            <td>{log.ip_address or ""}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;padding:30px;background:#f1f5f9;">
        <h1>DxCon Audit Center</h1>

        <table border="1" cellpadding="8"
               style="background:white;width:100%;border-collapse:collapse;">
            <tr>
                <th>Time</th>
                <th>User</th>
                <th>Action</th>
                <th>Object Type</th>
                <th>Object ID</th>
                <th>IP</th>
            </tr>

            {rows}
        </table>
    </body>
    </html>
    """
