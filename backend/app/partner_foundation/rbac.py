"""Organization role permission matrix — Sprint 005."""

from __future__ import annotations

ORG_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "ORG_OWNER": {
        "org.view", "org.create", "org.update", "org.delete",
        "user.view", "user.create", "user.update", "user.delete", "user.invite",
        "contract.view", "contract.create", "contract.update", "contract.delete", "contract.approve",
        "price.view", "price.create", "price.update", "price.delete", "price.import", "price.export",
        "data.view", "data.create", "data.update", "data.delete", "data.approve", "data.export", "data.import",
    },
    "CLINIC_ADMIN": {
        "org.view", "org.update",
        "user.view", "user.create", "user.update", "user.invite",
        "contract.view", "contract.create", "contract.update",
        "price.view", "price.create", "price.update", "price.export",
        "data.view", "data.create", "data.update", "data.approve", "data.export",
    },
    "DOCTOR": {
        "org.view", "data.view", "data.update", "data.approve", "data.export",
    },
    "RECEPTION": {
        "org.view", "data.view", "data.create", "data.update", "data.export",
    },
    "COLLECTOR": {
        "org.view", "data.view", "data.update",
    },
    "FINANCE": {
        "org.view", "contract.view", "price.view", "data.view", "data.export",
    },
    "VIEWER": {
        "org.view", "data.view",
    },
}

GLOBAL_ORG_BYPASS_ROLES = frozenset({"SUPER_ADMIN", "SYSTEM_ADMIN"})


def org_role_has_permission(role_code: str, permission: str) -> bool:
    perms = ORG_ROLE_PERMISSIONS.get(role_code or "", set())
    return permission in perms


def default_permissions_for_role(role_code: str) -> list[str]:
    return sorted(ORG_ROLE_PERMISSIONS.get(role_code, set()))
