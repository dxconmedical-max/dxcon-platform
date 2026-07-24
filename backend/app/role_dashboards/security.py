"""RBAC vocabulary for role dashboards."""

from __future__ import annotations

ADMIN_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "PLATFORM_ADMIN"})
RECEPTION_ROLES = frozenset({"RECEPTION", "RECEPTIONIST", "ADMIN", "SUPER_ADMIN"})
LAB_ROLES = frozenset({"LAB", "LAB_TECH", "LAB_SUPERVISOR", "LAB_MANAGER", "ADMIN", "SUPER_ADMIN", "DOCTOR"})
COLLECTOR_ROLES = frozenset({"COLLECTOR", "PARTNER_COLLECTOR", "DRIVER", "ADMIN", "SUPER_ADMIN"})
DOCTOR_ROLES = frozenset({"DOCTOR", "PHYSICIAN", "ADMIN", "SUPER_ADMIN"})
PATIENT_ROLES = frozenset({"PATIENT", "ADMIN", "SUPER_ADMIN"})

ROLE_DASHBOARD_ROLES: dict[str, frozenset[str]] = {
    "admin": ADMIN_ROLES,
    "administration": ADMIN_ROLES,
    "reception": RECEPTION_ROLES,
    "laboratory": LAB_ROLES,
    "lab": LAB_ROLES,
    "collector": COLLECTOR_ROLES,
    "doctor": DOCTOR_ROLES,
    "patient": PATIENT_ROLES,
}

# Aggregate KPI keys — never include patient name/phone/national_id.
SAFE_METRIC_KEYS = frozenset(
    {
        "orders_today",
        "pending_collection",
        "lab_queue",
        "overdue_tests",
        "avg_tat_minutes",
        "critical_results",
        "completed_reports",
        "operational_alerts",
        "pending_payment",
        "users",
        "tenants",
        "audit_events_today",
        "incoming",
        "testing",
        "pending_review",
        "released_today",
        "awaiting_collection",
        "in_transit",
        "arrived_at_lab",
        "pending_validation",
        "todays_patients",
        "waiting_queue",
        "new_registrations",
        "results_available",
        "appointments",
        "home_visits",
        "messages_unread",
    }
)
