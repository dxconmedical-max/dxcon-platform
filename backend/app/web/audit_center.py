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
            <td>{log.actor}</td>
            <td>{log.action}</td>
            <td>{log.entity_type}</td>
            <td>{log.entity_id}</td>
            <td>{log.details}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial;padding:30px;">
        <h1>DxCon Audit Center</h1>

        <table border="1" cellpadding="8"
               style="width:100%;border-collapse:collapse;">
            <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity</th>
                <th>ID</th>
                <th>Details</th>
            </tr>

            {rows}
        </table>
    </body>
    </html>
    """
