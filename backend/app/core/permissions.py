ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {"*"},
    "SYSTEM_ADMIN": {
        "users.read",
        "users.write",
        "security.read",
        "security.write",
        "reports.read",
        "mdm.read",
        "mdm.write",
    },
    "MASTER_DATA_ADMIN": {
        "mdm.read",
        "mdm.write",
        "reports.read",
    },
    "ADMIN": {
        "users.read",
        "users.write",
        "security.read",
        "security.write",
        "reports.read",
        "mdm.read",
    },
    "DOCTOR": {
        "patients.read",
        "results.read",
        "referrals.write",
        "mdm.read",
    },
    "LAB": {
        "results.read",
        "results.write",
        "samples.read",
        "mdm.read",
        "lab.read",
        "lab.write",
        "lab.receive",
        "lab.result_entry",
        "lab.qc",
        "lab.validate",
        "lis.import",
        "lis.read",
    },
    "COLLECTOR": {
        "collections.read",
        "collections.write",
        "mdm.read",
    },
    "RECEPTION": {
        "mdm.read",
        "reception.read",
        "reception.write",
        "patients.read",
        "patients.create",
        "patients.update",
        "orders.create",
        "orders.read",
        "payments.collect",
        "billing.read",
        "print.barcode",
        "print.invoice",
        "print.request_form",
    },
    "ACCOUNTING": {
        "billing.read",
        "billing.write",
        "payments.read",
        "mdm.read",
    },
    "PATIENT": {
        "profile.read",
        "profile.write",
        "results.read",
    },
}


def role_has_permission(role, permission):
    allowed = ROLE_PERMISSIONS.get(role or "", set())
    return "*" in allowed or permission in allowed


def get_role_permissions(role):
    allowed = ROLE_PERMISSIONS.get(role or "", set())
    if "*" in allowed:
        return sorted({permission for perms in ROLE_PERMISSIONS.values() for permission in perms if permission != "*"})
    return sorted(allowed)
