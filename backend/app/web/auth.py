from flask import Blueprint, request, redirect, session
import bcrypt

from app.models.user import User


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
    except:
        return False


def redirect_by_role(role):

    if role == "DOCTOR":
        return redirect("/doctor")

    if role == "COLLECTOR":
        return redirect("/collector")

    if role == "LAB_TECHNICIAN":
        return redirect("/samples")

    if role == "PATIENT":
        return redirect("/portal")

    return redirect("/dashboard")


@auth_web_bp.route("/login", methods=["GET", "POST"])
def login_page():

    error = ""

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

            return redirect_by_role(user.role)

    return f"""
    <html>
    <body style="font-family:Arial;background:#f1f5f9;padding:40px;">

        <h1>DxCon Login</h1>

        <p style="color:red;">{error}</p>

        <form method="POST">
            <input name="email" placeholder="Email" style="padding:10px;width:300px;">
            <br><br>

            <input name="password" type="password" placeholder="Password" style="padding:10px;width:300px;">
            <br><br>

            <button type="submit">Login</button>
        </form>

        <br>
        <a href="/portal">Patient Portal</a>

    </body>
    </html>
    """


@auth_web_bp.route("/logout")
def logout():

    session.clear()

    return redirect("/login")
