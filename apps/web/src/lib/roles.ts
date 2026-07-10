export type UserRole = string;

export const ROLE_WORKSPACE_ROUTES: Record<string, string> = {
  SUPER_ADMIN: "/app/admin",
  DXCON_ADMIN: "/app/admin",
  ADMIN: "/app/admin",
  SYSTEM_ADMIN: "/app/admin",
  EXECUTIVE: "/app/executive",
  RECEPTION: "/app/reception",
  PARTNER_RECEPTION: "/app/reception",
  DOCTOR: "/app/doctor",
  PARTNER_DOCTOR: "/app/doctor",
  PARTNER_CLINIC_DOCTOR: "/app/doctor",
  LAB_MANAGER: "/app/lab",
  LAB_SUPERVISOR: "/app/lab",
  LAB_TECHNICIAN: "/app/lab",
  PARTNER_LAB_MANAGER: "/app/lab",
  PARTNER_LAB_TECHNICIAN: "/app/lab",
  LAB: "/app/lab",
  COLLECTOR: "/app/collector",
  PARTNER_COLLECTOR: "/app/collector",
  DRIVER: "/app/collector",
  CLINIC_OWNER: "/app/clinic",
  CLINIC_ADMIN: "/app/clinic",
  PARTNER_OWNER: "/app/clinic",
  PARTNER_CLINIC_OWNER: "/app/clinic",
  PATIENT: "/app/patient",
};

export const DEFAULT_WORKSPACE = "/app";

export const WORKSPACE_ROUTES = [
  "/app",
  "/app/admin",
  "/app/executive",
  "/app/reception",
  "/app/doctor",
  "/app/lab",
  "/app/collector",
  "/app/clinic",
  "/app/patient",
] as const;

export type WorkspaceRoute = (typeof WORKSPACE_ROUTES)[number];

export function workspacePathForRole(role: string | null | undefined): string {
  return ROLE_WORKSPACE_ROUTES[(role ?? "").toUpperCase()] ?? DEFAULT_WORKSPACE;
}

export function roleLabel(role: string | null | undefined): string {
  const labels: Record<string, string> = {
    SUPER_ADMIN: "Super Admin",
    DXCON_ADMIN: "DxCon Admin",
    ADMIN: "Administrator",
    EXECUTIVE: "Executive",
    RECEPTION: "Reception",
    DOCTOR: "Doctor",
    PARTNER_DOCTOR: "Partner Doctor",
    LAB_MANAGER: "Lab Manager",
    LAB_TECHNICIAN: "Lab Technician",
    COLLECTOR: "Collector",
    CLINIC_OWNER: "Clinic Owner",
    PATIENT: "Patient",
  };
  return labels[(role ?? "").toUpperCase()] ?? role ?? "User";
}

export function isWorkspacePath(path: string): boolean {
  return WORKSPACE_ROUTES.some(
    (route) => path === route || path.startsWith(`${route}/`),
  );
}
