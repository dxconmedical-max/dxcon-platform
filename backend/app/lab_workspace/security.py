"""Lab workspace RBAC and workflow contracts."""

LAB_READ_ROLES = frozenset(
    {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB", "LAB_TECHNICIAN", "DOCTOR"}
)
LAB_WRITE_ROLES = frozenset(
    {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB", "LAB_TECHNICIAN"}
)
LAB_SUPERVISOR_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB"})
LAB_MEDICAL_ROLES = frozenset(
    {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "DOCTOR"}
)
# Lab + doctor may release approved results; patients read via patient portal / release html.
LAB_RELEASE_ROLES = frozenset(
    {"SUPER_ADMIN", "SYSTEM_ADMIN", "ADMIN", "LAB", "DOCTOR"}
)
LAB_PATIENT_REPORT_ROLES = frozenset(
    {
        "SUPER_ADMIN",
        "SYSTEM_ADMIN",
        "ADMIN",
        "LAB",
        "LAB_TECHNICIAN",
        "DOCTOR",
        "PATIENT",
    }
)
LAB_ADMIN_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN"})

LAB_FORBIDDEN_TECH = frozenset({"report.release", "doctor.approve", "connector.secrets"})

# Specimen condition / rejection reasons (structured).
CONDITION_STATUSES = (
    "acceptable",
    "hemolyzed",
    "insufficient_volume",
    "wrong_tube",
    "damaged",
    "clotted",
    "mislabeled",
    "rejected",
)

REJECTION_REASONS = (
    "hemolyzed",
    "insufficient_volume",
    "wrong_tube",
    "damaged",
    "clotted",
    "mislabeled",
    "patient_mismatch",
    "order_mismatch",
    "expired",
    "other",
)

# Accession / processing stage tracked on LabAccessionRecord.processing_status
PROCESSING_STATUSES = (
    "awaiting_receipt",
    "received",
    "rejected",
    "accessioned",
    "assigned",
    "processing",
    "results_entered",
    "tech_validated",
    "medically_validated",
)

# Result workflow_status on BizResult
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
    "analyzer",
)

# After technical or medical validation, result values are locked.
LOCKED_RESULT_WORKFLOW = frozenset(
    {"pending_review", "approved", "released"}
)
LOCKED_ORDER_STATUSES = frozenset({"approved", "released"})

LAB_STATUS_FLOW = (
    "in_transit",
    "lab_received",
    "accessioned",
    "assigned",
    "processing",
    "testing",
    "pending_review",
    "approved",
)

LAB_STATUS_EXCEPTIONS = ("rejected", "cancelled")
