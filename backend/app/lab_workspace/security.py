"""Lab workspace RBAC — Sprint 007."""

LAB_READ_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB", "LAB_TECHNICIAN", "DOCTOR"})
LAB_WRITE_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB", "LAB_TECHNICIAN"})
LAB_SUPERVISOR_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB"})
LAB_ADMIN_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN"})

LAB_FORBIDDEN_TECH = frozenset({"report.release", "doctor.approve", "connector.secrets"})

CONDITION_STATUSES = (
    "acceptable",
    "hemolyzed",
    "insufficient_volume",
    "wrong_tube",
    "damaged",
    "rejected",
)

RESULT_WORKFLOW_STATUSES = (
    "draft",
    "entered",
    "qc_pending",
    "qc_passed",
    "validation_required",
    "pending_review",
    "approved",
    "released",
    "imported",
)
