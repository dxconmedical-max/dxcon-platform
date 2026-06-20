from functools import wraps
from flask import redirect, session

def web_roles_required(*roles):

    def decorator(fn):

        @wraps(fn)
        def wrapper(*args, **kwargs):

            role = session.get("role")

            if role not in roles:
                return redirect("/login")

            return fn(*args, **kwargs)

        return wrapper

    return decorator
