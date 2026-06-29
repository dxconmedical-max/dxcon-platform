import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.core.statuses import (
    NOTIFICATION_CHANNEL_EMAIL,
    NOTIFICATION_CHANNEL_IN_APP,
    NOTIFICATION_CHANNEL_PUSH,
    NOTIFICATION_CHANNEL_SMS,
    NOTIFICATION_CHANNEL_ZALO,
    NOTIFICATION_TEMPLATE_ACTIVE,
    NOTIFICATION_TEMPLATE_APPOINTMENT_REMINDER,
    NOTIFICATION_TEMPLATE_CRITICAL_RESULT,
    NOTIFICATION_TEMPLATE_INVOICE,
    NOTIFICATION_TEMPLATE_PASSWORD_RESET,
    NOTIFICATION_TEMPLATE_PAYMENT_SUCCESS,
    NOTIFICATION_TEMPLATE_RESULT_READY,
    NOTIFICATION_TEMPLATE_SAMPLE_COLLECTION_REMINDER,
    NOTIFICATION_TEMPLATE_WELCOME,
)
from app.extensions.db import db
from app.models.notification_template import NotificationTemplate


def seed_notifications_demo():
    if NotificationTemplate.query.first():
        return {"templates_seeded": 0, "already_seeded": True}

    templates = [
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_RESULT_READY,
            name="Result Ready",
            subject="Your lab result is ready",
            body="Hello {name}, your result for order {order_code} is ready to view.",
            sms_body="DxCon: Ket qua {order_code} da san sang.",
            push_title="Result Ready",
            push_body="Your result for {order_code} is ready.",
            zalo_body="Ket qua xet nghiem {order_code} da san sang tren DxCon.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_EMAIL},{NOTIFICATION_CHANNEL_PUSH}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_APPOINTMENT_REMINDER,
            name="Appointment Reminder",
            subject="Appointment reminder",
            body="Reminder: your appointment is scheduled for {appointment_time}.",
            sms_body="DxCon: Nhac lich hen {appointment_time}.",
            push_title="Appointment Reminder",
            push_body="Your appointment is at {appointment_time}.",
            zalo_body="Nhac lich hen luc {appointment_time}.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_SMS},{NOTIFICATION_CHANNEL_ZALO}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_SAMPLE_COLLECTION_REMINDER,
            name="Sample Collection Reminder",
            subject="Sample collection reminder",
            body="Collector will arrive around {collection_time} for order {order_code}.",
            sms_body="DxCon: Thu mau cho don {order_code} luc {collection_time}.",
            push_title="Sample Collection",
            push_body="Collector arriving for {order_code}.",
            zalo_body="Thu mau cho don {order_code} luc {collection_time}.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_SMS}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_PAYMENT_SUCCESS,
            name="Payment Success",
            subject="Payment received",
            body="Payment of {amount} for invoice {invoice_no} was successful.",
            sms_body="DxCon: Thanh toan {amount} thanh cong.",
            push_title="Payment Success",
            push_body="Payment {amount} received.",
            zalo_body="Thanh toan {amount} thanh cong.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_EMAIL}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_INVOICE,
            name="Invoice",
            subject="Invoice {invoice_no}",
            body="Invoice {invoice_no} for {amount} is available.",
            sms_body="DxCon: Hoa don {invoice_no} - {amount}.",
            push_title="Invoice Ready",
            push_body="Invoice {invoice_no} is ready.",
            zalo_body="Hoa don {invoice_no} da phat hanh.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_EMAIL}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_CRITICAL_RESULT,
            name="Critical Result",
            subject="Critical result alert",
            body="Critical result detected for {test_name}. Physician notification required.",
            sms_body="DxCon: CANH BAO ket qua nguy hiem {test_name}.",
            push_title="Critical Result",
            push_body="Critical value for {test_name}.",
            zalo_body="Canh bao ket qua nguy hiem {test_name}.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_SMS},{NOTIFICATION_CHANNEL_EMAIL},{NOTIFICATION_CHANNEL_PUSH},{NOTIFICATION_CHANNEL_ZALO}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_WELCOME,
            name="Welcome",
            subject="Welcome to DxCon",
            body="Welcome {name}! Your DxCon account is ready.",
            sms_body="Chao mung {name} den voi DxCon.",
            push_title="Welcome",
            push_body="Welcome to DxCon, {name}.",
            zalo_body="Chao mung {name} den voi DxCon.",
            default_channels=f"{NOTIFICATION_CHANNEL_IN_APP},{NOTIFICATION_CHANNEL_EMAIL}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
        NotificationTemplate(
            template_code=NOTIFICATION_TEMPLATE_PASSWORD_RESET,
            name="Password Reset",
            subject="Reset your password",
            body="Use this link to reset your password: {reset_link}",
            sms_body="Ma dat lai mat khau DxCon: {reset_code}",
            push_title="Password Reset",
            push_body="Reset your DxCon password.",
            zalo_body="Dat lai mat khau DxCon: {reset_link}",
            default_channels=f"{NOTIFICATION_CHANNEL_EMAIL},{NOTIFICATION_CHANNEL_SMS}",
            status=NOTIFICATION_TEMPLATE_ACTIVE,
        ),
    ]

    for template in templates:
        db.session.add(template)
    db.session.commit()
    return {"templates_seeded": len(templates)}


def main():
    from app import create_app

    app = create_app()
    with app.app_context():
        db.create_all()
        summary = seed_notifications_demo()
        print("\n=== DXCON NOTIFICATIONS DEMO SEED ===\n")
        for key, value in summary.items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
