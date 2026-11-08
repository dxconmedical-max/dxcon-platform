"""Reporting engine RBAC — Sprint 008."""

REPORT_READ_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "DOCTOR", "LAB", "RECEPTION"})
DOCTOR_APPROVE_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "DOCTOR", "LAB"})
DOCTOR_RELEASE_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "DOCTOR"})
REPORT_WRITE_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "DOCTOR", "LAB"})
# PATIENT removed: no patient-login-to-patient-record link exists yet, so it could read any patient.
PATIENT_REPORT_ROLES = frozenset({"SUPER_ADMIN", "ADMIN"})

FORBIDDEN_APPROVE = frozenset({"RECEPTION", "LAB_TECHNICIAN", "PATIENT", "COLLECTOR"})
