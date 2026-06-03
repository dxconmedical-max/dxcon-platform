from flask import Blueprint, request

from app.extensions.db import db
from app.models.patient import Patient


patients_bp = Blueprint(
    "patients",
    __name__,
    url_prefix="/api/v1/patients"
)


@patients_bp.route("", methods=["GET"])
def get_patients():

    patients = Patient.query.all()

    return {
        "count": len(patients),
        "patients": [
            patient.to_dict()
            for patient in patients
        ]
    }


@patients_bp.route("", methods=["POST"])
def create_patient():

    data = request.get_json()

    patient = Patient(
        patient_code=data.get("patient_code"),
        full_name=data.get("full_name"),
        gender=data.get("gender"),
        date_of_birth=data.get("date_of_birth"),
        phone=data.get("phone"),
        email=data.get("email"),
        address=data.get("address"),
        national_id=data.get("national_id")
    )

    db.session.add(patient)
    db.session.commit()

    return {
        "message": "Patient created successfully",
        "patient": patient.to_dict()
    }, 201


@patients_bp.route("/<patient_id>", methods=["GET"])
def get_patient(patient_id):

    patient = Patient.query.get(patient_id)

    if not patient:
        return {
            "error": "Patient not found"
        }, 404

    return patient.to_dict()


@patients_bp.route("/<patient_id>", methods=["PUT"])
def update_patient(patient_id):

    patient = Patient.query.get(patient_id)

    if not patient:
        return {
            "error": "Patient not found"
        }, 404

    data = request.get_json()

    patient.full_name = data.get(
        "full_name",
        patient.full_name
    )

    patient.gender = data.get(
        "gender",
        patient.gender
    )

    patient.date_of_birth = data.get(
        "date_of_birth",
        patient.date_of_birth
    )

    patient.phone = data.get(
        "phone",
        patient.phone
    )

    patient.email = data.get(
        "email",
        patient.email
    )

    patient.address = data.get(
        "address",
        patient.address
    )

    patient.national_id = data.get(
        "national_id",
        patient.national_id
    )

    db.session.commit()

    return {
        "message": "Patient updated successfully",
        "patient": patient.to_dict()
    }


@patients_bp.route("/<patient_id>", methods=["DELETE"])
def delete_patient(patient_id):

    patient = Patient.query.get(patient_id)

    if not patient:
        return {
            "error": "Patient not found"
        }, 404

    db.session.delete(patient)
    db.session.commit()

    return {
        "message": "Patient deleted successfully"
    }
