from functools import wraps
from flask import session, redirect


def web_roles_required(*allowed_roles):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            role = session.get("role")

            if role not in allowed_roles:
                return redirect("/login")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
