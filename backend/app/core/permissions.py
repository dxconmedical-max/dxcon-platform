ROLE_PERMISSIONS = {
    "SUPER_ADMIN": {"*"},
    "ADMIN": {
        "users.read",
        "users.write",
        "security.read",
        "security.write",
        "reports.read",
    },
    "DOCTOR": {
        "patients.read",
        "results.read",
        "referrals.write",
    },
    "LAB": {
        "results.read",
        "results.write",
        "samples.read",
    },
    "COLLECTOR": {
        "collections.read",
        "collections.write",
    },
    "ACCOUNTING": {
        "billing.read",
        "billing.write",
        "payments.read",
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
