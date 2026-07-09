"""Role → workspace routing — Sprint 011."""

from __future__ import annotations

ROLE_WORKSPACE_ROUTES: dict[str, str] = {
    "SUPER_ADMIN": "/app/admin",
    "DXCON_ADMIN": "/app/admin",
    "ADMIN": "/app/admin",
    "SYSTEM_ADMIN": "/app/admin",
    "EXECUTIVE": "/app/executive",
    "RECEPTION": "/app/reception",
    "DOCTOR": "/app/doctor",
    "PARTNER_DOCTOR": "/app/doctor",
    "LAB_MANAGER": "/app/lab",
    "LAB_TECHNICIAN": "/app/lab",
    "LAB": "/app/lab",
    "COLLECTOR": "/app/collector",
    "DRIVER": "/app/collector",
    "CLINIC_OWNER": "/app/clinic",
    "CLINIC_ADMIN": "/app/clinic",
    "PATIENT": "/app/patient",
}

DEFAULT_WORKSPACE = "/app"

WORKSPACE_HOME_ROUTES = (
    "/app",
    "/app/admin",
    "/app/executive",
    "/app/reception",
    "/app/doctor",
    "/app/lab",
    "/app/collector",
    "/app/clinic",
    "/app/patient",
)


def workspace_path_for_role(role: str | None) -> str:
    return ROLE_WORKSPACE_ROUTES.get((role or "").upper(), DEFAULT_WORKSPACE)
