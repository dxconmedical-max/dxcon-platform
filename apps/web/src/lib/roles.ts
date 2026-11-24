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
  CLINIC_VIEWER: "/app/clinic-results",
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
  "/app/clinic-results",
] as const;

export type WorkspaceRoute = (typeof WORKSPACE_ROUTES)[number];

export function workspacePathForRole(role: string | null | undefined): string {
  return ROLE_WORKSPACE_ROUTES[(role ?? "").toUpperCase()] ?? DEFAULT_WORKSPACE;
}

export function roleLabel(role: string | null | undefined): string {
  const labels: Record<string, string> = {
    SUPER_ADMIN: "Quản trị tối cao",
    DXCON_ADMIN: "Quản trị DxCon",
    ADMIN: "Quản trị viên",
    EXECUTIVE: "Điều hành",
    RECEPTION: "Tiếp nhận",
    DOCTOR: "Bác sĩ",
    PARTNER_DOCTOR: "Bác sĩ đối tác",
    LAB_MANAGER: "Trưởng phòng xét nghiệm",
    LAB_TECHNICIAN: "Kỹ thuật viên xét nghiệm",
    COLLECTOR: "Nhân viên thu mẫu",
    CLINIC_OWNER: "Chủ phòng khám",
    PATIENT: "Bệnh nhân",
  };
  return labels[(role ?? "").toUpperCase()] ?? role ?? "Người dùng";
}

export function isWorkspacePath(path: string): boolean {
  return WORKSPACE_ROUTES.some(
    (route) => path === route || path.startsWith(`${route}/`),
  );
}
