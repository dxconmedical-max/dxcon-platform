from flask import Blueprint

from app.core.authz import roles_required
from app.core.roles import ADMIN, SUPER_ADMIN
from app.models.user import User

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/v1/admin"
)


@admin_bp.route("/users", methods=["GET"])
@roles_required(SUPER_ADMIN, ADMIN)
def get_users():
    """List users — requires authenticated admin (P0-A / P0-3)."""
    users = User.query.all()

    return {
        "count": len(users),
        "users": [
            user.to_dict()
            for user in users
        ]
    }
