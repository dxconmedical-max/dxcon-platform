"use client";

import type { LucideIcon } from "lucide-react";
import {
  Building2,
  FlaskConical,
  LayoutDashboard,
  Settings,
  Stethoscope,
  Truck,
  UserCircle,
} from "lucide-react";

import { can } from "@/lib/permissions";
import type { AuthCapabilities } from "@/services/auth";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
  permission?: string;
  feature?: string;
  workspaces?: string[];
};

const ALL_NAV: NavItem[] = [
  { href: "/app", label: "Overview", icon: LayoutDashboard },
  {
    href: "/app/admin",
    label: "Administration",
    icon: Settings,
    permission: "users.read",
    workspaces: ["/app/admin"],
  },
  {
    href: "/app/executive",
    label: "Executive",
    icon: LayoutDashboard,
    permission: "executive.read",
    workspaces: ["/app/executive"],
  },
  {
    href: "/app/reception",
    label: "Reception",
    icon: Building2,
    permission: "reception.read",
    workspaces: ["/app/reception"],
  },
  {
    href: "/app/doctor",
    label: "Doctor",
    icon: Stethoscope,
    permission: "portal.doctor.read",
    workspaces: ["/app/doctor"],
  },
  {
    href: "/app/patient",
    label: "Patient",
    icon: UserCircle,
    permission: "portal.patient.read",
    workspaces: ["/app/patient"],
  },
  {
    href: "/app/lab",
    label: "Laboratory",
    icon: FlaskConical,
    permission: "lab.read",
    workspaces: ["/app/lab"],
  },
  {
    href: "/app/collector",
    label: "Collector",
    icon: Truck,
    permission: "collections.read",
    workspaces: ["/app/collector"],
  },
  {
    href: "/app/clinic",
    label: "Clinic",
    icon: Building2,
    permission: "data.view",
    workspaces: ["/app/clinic"],
  },
];

export function buildNavItems(capabilities: AuthCapabilities | null): NavItem[] {
  if (!capabilities) return [ALL_NAV[0]];

  const workspace = capabilities.workspace;
  const adminRoles = new Set(["SUPER_ADMIN", "DXCON_ADMIN", "ADMIN", "SYSTEM_ADMIN"]);
  const isAdmin = adminRoles.has((capabilities.user.role ?? "").toUpperCase());
  const hasWildcard = (capabilities.permissions ?? []).includes("*");

  return ALL_NAV.filter((item) => {
    if (item.href === "/app") return true;
    if (isAdmin || hasWildcard) return true;
    if (item.workspaces && !item.workspaces.includes(workspace)) {
      if (item.href !== workspace) return false;
    }
    if (item.permission && !can(capabilities, item.permission) && !hasWildcard) {
      return item.workspaces?.includes(workspace) ?? false;
    }
    if (item.feature && !(capabilities.features ?? []).includes(item.feature)) {
      return false;
    }
    return item.workspaces?.includes(workspace) ?? true;
  });
}
