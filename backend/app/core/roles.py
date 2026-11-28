SUPER_ADMIN = "SUPER_ADMIN"
ADMIN = "ADMIN"
DOCTOR = "DOCTOR"
LAB = "LAB"
COLLECTOR = "COLLECTOR"
ACCOUNTING = "ACCOUNTING"
PATIENT = "PATIENT"

RECEPTION = "RECEPTION"
SALE = "SALE"  # sales staff: sees only the customer accounts they own
CLINIC_ADMIN = "CLINIC_ADMIN"  # clinic-side account that submits order slips for its own clinic

ALL_ROLES = [
    SUPER_ADMIN,
    ADMIN,
    DOCTOR,
    LAB,
    COLLECTOR,
    ACCOUNTING,
    PATIENT,
    RECEPTION,
    CLINIC_ADMIN,
    SALE,
]
