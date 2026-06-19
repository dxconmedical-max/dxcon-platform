from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roles_required(*allowed_roles):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            verify_jwt_in_request()

            claims = get_jwt()

            role = claims.get("role")

            if role not in allowed_roles:
                return {
                    "error": "forbidden",
                    "required_roles": list(allowed_roles),
                    "your_role": role
                }, 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
