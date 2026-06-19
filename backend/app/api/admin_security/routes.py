from flask import Blueprint

from app.core.authz import roles_required
from app.core.roles import SUPER_ADMIN, ADMIN


admin_security_bp = Blueprint(
    "admin_security_bp",
    __name__,
    url_prefix="/api/v1/admin-security"
)


@admin_security_bp.route("/health")
@roles_required(
    SUPER_ADMIN,
    ADMIN
)
def secure_health():

    return {
        "status": "ok",
        "module": "admin-security"
    }
