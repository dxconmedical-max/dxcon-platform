from functools import wraps
from flask import session, redirect


def login_required(func):

    @wraps(func)
    def wrapper(*args, **kwargs):

        if not session.get("user_id"):
            return redirect("/login")

        return func(*args, **kwargs)

    return wrapper


def role_required(*roles):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):

            if not session.get("user_id"):
                return redirect("/login")

            role = session.get("role")

            if role not in roles:
                return f"""
                <html>
                <body style="font-family:Arial;background:#f1f5f9;padding:40px;">
                    <h2>Access Denied</h2>
                    <p>Your role: {role}</p>
                    <p>Allowed roles: {", ".join(roles)}</p>
                    <a href="/dashboard">Back to Dashboard</a>
                </body>
                </html>
                """

            return func(*args, **kwargs)

        return wrapper

    return decorator
