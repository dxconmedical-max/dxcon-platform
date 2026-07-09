from flask import Blueprint, current_app, redirect, request, session

import bcrypt

from app.core.passwords import verify_password as verify_password_hash
from app.models.patient import Patient
from app.models.user import User
from app.web.launch_ui_lib import (
    DEMO_ROLE_HINTS,
    demo_role_dashboard,
    render_login_page,
)
from app.web_gateway.routing import workspace_path_for_role
from app.web_gateway.session import (
    clear_session,
    configure_remember_me,
    establish_session,
    is_authenticated,
    redirect_if_authenticated,
)

auth_web_bp = Blueprint("auth_web", __name__)


def verify_password(stored_password, input_password):
    if verify_password_hash(stored_password, input_password):
        return True
    try:
        return bcrypt.checkpw(
            input_password.encode("utf-8"),
            stored_password.encode("utf-8"),
        )
    except (ValueError, TypeError, AttributeError):
        return False


def attach_patient_to_session(user):
    if user.role != "PATIENT":
        return

    patient = None
    if user.phone:
        patient = Patient.query.filter_by(phone=user.phone).first()
    if not patient:
        patient = Patient.query.filter_by(email=user.email).first()
    if patient:
        session["patient_id"] = patient.id
        session["patient_code"] = patient.patient_code
        session["patient_name"] = patient.full_name


def redirect_by_role(role):
    return redirect(workspace_path_for_role(role))


@auth_web_bp.route("/login", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        redirect_response = redirect_if_authenticated()
        if redirect_response:
            return redirect_response

    error = ""
    role_hint = request.args.get("role", "")
    expired = request.args.get("expired") == "1"

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        remember = request.form.get("remember") == "1"
        configure_remember_me(current_app._get_current_object(), remember)

        user = User.query.filter_by(email=email).first()

        if not user:
            error = "Invalid email or password"
        elif not user.is_active:
            error = "User is inactive"
        elif not verify_password(user.password_hash, password):
            error = "Invalid email or password"
        else:
            establish_session(
                user_id=user.id,
                role=user.role,
                email=user.email,
                remember=remember,
            )
            attach_patient_to_session(user)
            return redirect_by_role(user.role)

    return render_login_page(error=error, role_hint=role_hint, expired=expired)


@auth_web_bp.route("/login/demo")
def demo_login_page():
    from app.web_gateway.config import demo_mode_enabled

    if not demo_mode_enabled():
        return redirect("/login")

    role = (request.args.get("role") or "ADMIN").upper()
    email = DEMO_ROLE_HINTS.get(role, DEMO_ROLE_HINTS["ADMIN"])

    user = User.query.filter_by(email=email).first()
    if not user:
        user = User.query.filter(User.role == role).first()
    if not user and role == "ADMIN":
        user = User.query.filter(User.role.in_(("ADMIN", "SUPER_ADMIN"))).first()

    if user and user.is_active:
        establish_session(user_id=user.id, role=user.role, email=user.email)
        attach_patient_to_session(user)
    else:
        session["user_id"] = f"demo-{role.lower()}"
        session["role"] = role
        session["email"] = email
        session["demo_mode"] = True

    return redirect(demo_role_dashboard(role))


@auth_web_bp.route("/logout")
def logout():
    clear_session()
    return redirect("/login")
