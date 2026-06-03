from flask import Blueprint

from app.models.user import User

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/v1/admin"
)


@admin_bp.route("/users", methods=["GET"])
def get_users():

    users = User.query.all()

    return {
        "count": len(users),
        "users": [
            user.to_dict()
            for user in users
        ]
    }
