from flask import Blueprint, request
from flask_jwt_extended import create_access_token

from app.extensions.db import db
from app.models.user import User

from app.core.passwords import (
    hash_password,
    verify_password
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    email = data.get("email")
    phone = data.get("phone")
    password = data.get("password")
    role = data.get("role", "PATIENT")

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return {
            "error": "Email already exists"
        }, 400

    user = User(
        email=email,
        phone=phone,
        role=role,
        password_hash=hash_password(password)
    )

    db.session.add(user)
    db.session.commit()

    return {
        "message": "User created successfully",
        "role": role
    }, 201


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(
        email=email
    ).first()

    if not user:
        return {
            "error": "Invalid credentials"
        }, 401

    if not verify_password(
        user.password_hash,
        password
    ):
        return {
            "error": "Invalid credentials"
        }, 401

    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            "role": user.role,
            "email": user.email
        }
    )

    return {
        "success": True,
        "token": access_token,
        "access_token": access_token,
        "email": user.email,
        "role": user.role,
        "user": user.to_dict()
    }
