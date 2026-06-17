import os

from app import create_app
from app.extensions.db import db

app = create_app()

with app.app_context():
    db.create_all()
from app.models.user import User
from app.models.patient import Patient

with app.app_context():

    user = User.query.filter_by(
        email="patient@example.com"
    ).first()

    if not user:
        user = User(
            email="patient@example.com",
            phone="0901234567",
            password_hash="123456",
            role="PATIENT",
            is_active=True
        )
        db.session.add(user)

    patient = Patient.query.filter_by(
        phone="0901234567"
    ).first()

    if not patient:
        patient = Patient(
            patient_code="PT001",
            full_name="Nguyen Van A",
            phone="0901234567",
            email="patient@example.com",
            gender="MALE",
            address="Ho Chi Minh City"
        )
        db.session.add(patient)

    db.session.commit()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=os.getenv("APP_ENV", "development") != "production"
    )
