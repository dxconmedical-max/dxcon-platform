"""Reception workspace RBAC — Sprint 006."""

RECEPTION_READ_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "RECEPTION", "SYSTEM_ADMIN"})
RECEPTION_WRITE_ROLES = frozenset({"SUPER_ADMIN", "ADMIN", "RECEPTION", "SYSTEM_ADMIN"})

RECEPTION_FORBIDDEN_ACTIONS = frozenset({
    "patient.delete",
    "order.delete",
    "report.modify_released",
    "finance.modify_history",
})
