"""Sample Collection production workspace — auth roles."""

COLLECTION_READ_ROLES = frozenset({
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "ADMIN",
    "RECEPTION",
    "RECEPTIONIST",
    "PARTNER_RECEPTION",
    "COLLECTOR",
    "PARTNER_COLLECTOR",
    "DRIVER",
    "LAB",
    "LAB_TECHNICIAN",
    "LAB_MANAGER",
})

COLLECTION_WRITE_ROLES = frozenset({
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "ADMIN",
    "RECEPTION",
    "RECEPTIONIST",
    "PARTNER_RECEPTION",
    "COLLECTOR",
    "PARTNER_COLLECTOR",
    "DRIVER",
})

COLLECTION_SUPERVISOR_ROLES = frozenset({
    "SUPER_ADMIN",
    "SYSTEM_ADMIN",
    "ADMIN",
    "LAB_MANAGER",
})
