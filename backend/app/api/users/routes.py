from flask import Blueprint

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/api/v1/users"
)

@users_bp.route("/", methods=["GET"])
def get_users():

    return {
        "message": "Users API working"
    }
