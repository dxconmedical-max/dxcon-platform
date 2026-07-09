"""Session helpers for production web gateway — Sprint 011."""

from __future__ import annotations

from datetime import timedelta

from flask import redirect, session

from app.web_gateway.routing import workspace_path_for_role


def is_authenticated() -> bool:
    return bool(session.get("user_id"))


def establish_session(
    *,
    user_id,
    role: str,
    email: str,
    remember: bool = False,
    access_token: str | None = None,
    refresh_token: str | None = None,
) -> None:
    session["user_id"] = user_id
    session["role"] = role
    session["email"] = email
    session.permanent = remember
    if access_token:
        session["access_token"] = access_token
    if refresh_token:
        session["refresh_token"] = refresh_token


def clear_session() -> None:
    session.clear()


def redirect_if_authenticated():
    if is_authenticated():
        return redirect(workspace_path_for_role(session.get("role")))
    return None


def configure_remember_me(app, remember: bool) -> None:
    if remember:
        days = int(app.config.get("REMEMBER_ME_DAYS", "14"))
        app.permanent_session_lifetime = timedelta(days=days)
