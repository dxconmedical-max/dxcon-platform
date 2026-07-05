from flask import Blueprint, redirect, request, session

from app.models.patient import Patient
from app.models.user import User
from app.web.launch_ui_lib import render_login_page
import bcrypt

auth_web_bp = Blueprint("auth_web", __name__)


def verify_password(stored_password, input_password):

    if not stored_password:
        return False

    if stored_password == input_password:
        return True

    try:
        return bcrypt.checkpw(
            input_password.encode("utf-8"),
            stored_password.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def attach_patient_to_session(user):

    if user.role != "PATIENT":
        return

    patient = None

    if user.phone:
        patient = Patient.query.filter_by(
            phone=user.phone
        ).first()

    if not patient:
        patient = Patient.query.filter_by(
            email=user.email
        ).first()

    if patient:
        session["patient_id"] = patient.id
        session["patient_code"] = patient.patient_code
        session["patient_name"] = patient.full_name


def redirect_by_role(role):

    if role == "DOCTOR":
        return redirect("/app/doctor")

    if role == "RECEPTION":
        return redirect("/app/reception")

    if role == "COLLECTOR":
        return redirect("/app/collector")

    if role in ("LAB", "LAB_TECHNICIAN"):
        return redirect("/app/lab")

    if role == "PATIENT":
        return redirect("/app/patient")

    if role in ("ADMIN", "SUPER_ADMIN"):
        return redirect("/app/executive")

    return redirect("/app/system")


@auth_web_bp.route("/login", methods=["GET", "POST"])
def login_page():

    error = ""
    role_hint = request.args.get("role", "")

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if not user:
            error = "Invalid email or password"

        elif not user.is_active:
            error = "User is inactive"

        elif not verify_password(user.password_hash, password):
            error = "Invalid email or password"

        else:
            session["user_id"] = user.id
            session["role"] = user.role
            session["email"] = user.email

            attach_patient_to_session(user)

            return redirect_by_role(user.role)

    return render_login_page(error=error, role_hint=role_hint)


@auth_web_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
