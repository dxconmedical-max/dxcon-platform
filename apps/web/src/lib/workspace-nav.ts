import type { LucideIcon } from "lucide-react";
import {
  Building2,
  ClipboardList,
  FileText,
  FlaskConical,
  LayoutDashboard,
  Settings,
  Truck,
  UserCircle,
  Users,
} from "lucide-react";

import { can, hasFeature } from "@/lib/permissions";
import type { AuthCapabilities } from "@/services/auth";
export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  permission?: string;
  feature?: string;
  workspaces?: string[];
};

type WorkspaceNavItem = NavItem & { workspaces: string[] };

const WORKSPACE_NAV: WorkspaceNavItem[] = [
  { href: "/app/admin", label: "Dashboard", icon: LayoutDashboard, workspaces: ["/app/admin"] },
  { href: "/app/admin/organizations", label: "Organizations", icon: Building2, permission: "users.read", workspaces: ["/app/admin"] },
  { href: "/app/admin/patients", label: "Patients", icon: Users, permission: "users.read", workspaces: ["/app/admin"] },
  { href: "/app/admin/orders", label: "Orders", icon: ClipboardList, permission: "users.read", workspaces: ["/app/admin"] },
  { href: "/app/admin/integrations", label: "Integrations", icon: Settings, permission: "users.read", workspaces: ["/app/admin"] },
  { href: "/app/operations", label: "System Health", icon: LayoutDashboard, permission: "executive.read", workspaces: ["/app/admin", "/app/executive"] },
  { href: "/app/executive", label: "Dashboard", icon: LayoutDashboard, permission: "executive.read", workspaces: ["/app/executive"] },
  { href: "/app/reception", label: "Dashboard", icon: LayoutDashboard, permission: "reception.read", workspaces: ["/app/reception"] },
  { href: "/app/doctor", label: "Dashboard", icon: LayoutDashboard, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/patients", label: "Patients", icon: Users, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/orders", label: "Orders", icon: ClipboardList, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/reports", label: "Reports", icon: FileText, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/clinic", label: "Dashboard", icon: LayoutDashboard, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/patients", label: "Patients", icon: Users, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/orders", label: "Orders", icon: ClipboardList, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/reports", label: "Reports", icon: FileText, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/lab", label: "Dashboard", icon: LayoutDashboard, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/samples", label: "Work Queue", icon: FlaskConical, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/collector", label: "Dashboard", icon: LayoutDashboard, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/collector/jobs", label: "Assigned Jobs", icon: Truck, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/patient", label: "Dashboard", icon: LayoutDashboard, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/orders", label: "Orders", icon: ClipboardList, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/results", label: "Results", icon: FileText, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/bookings", label: "Bookings", icon: UserCircle, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/payments", label: "Payments", icon: ClipboardList, permission: "portal.patient.read", workspaces: ["/app/patient"] },
];

export function buildWorkspaceNavItems(capabilities: AuthCapabilities | null): NavItem[] {
  if (!capabilities) {
    return [{ href: "/app", label: "Overview", icon: LayoutDashboard }];
  }

  const workspace = capabilities.workspace;
  const adminRoles = new Set(["SUPER_ADMIN", "DXCON_ADMIN", "ADMIN", "SYSTEM_ADMIN"]);
  const role = (capabilities.user.role ?? "").toUpperCase();
  const isAdmin = adminRoles.has(role);
  const hasWildcard = (capabilities.permissions ?? []).includes("*");

  const items = WORKSPACE_NAV.filter((item) => {
    if (!item.workspaces.includes(workspace) && !isAdmin && !hasWildcard) {
      return false;
    }
    if (item.permission && !can(capabilities, item.permission) && !isAdmin && !hasWildcard) {
      return false;
    }
    if (item.feature && !hasFeature(capabilities, item.feature)) {
      return false;
    }
    return true;
  });

  if (items.length > 0) {
    return items;
  }

  return [{ href: workspace || "/app", label: "Dashboard", icon: LayoutDashboard }];
}
