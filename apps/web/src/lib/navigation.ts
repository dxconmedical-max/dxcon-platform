"use client";

import type { LucideIcon } from "lucide-react";
import {
  Building2,
  FlaskConical,
  LayoutDashboard,
  MapPin,
  Settings,
  ShieldCheck,
  Stethoscope,
  Truck,
  UserCircle,
  Users,
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
  { href: "/app", label: "Tổng quan", icon: LayoutDashboard },
  {
    href: "/app/admin",
    label: "Quản trị",
    icon: ShieldCheck,
    permission: "users.read",
    workspaces: ["/app/admin"],
  },
  {
    href: "/app/admin/organizations",
    label: "Tổ chức",
    icon: Building2,
    permission: "users.read",
    workspaces: ["/app/admin"],
  },
  {
    href: "/app/admin/integrations",
    label: "Tích hợp",
    icon: Settings,
    permission: "users.read",
    workspaces: ["/app/admin"],
  },
  {
    href: "/app/operations",
    label: "Vận hành",
    icon: LayoutDashboard,
    permission: "executive.read",
    workspaces: ["/app/admin", "/app/executive"],
  },
  {
    href: "/app/operations/live-map",
    label: "Bản đồ trực tiếp",
    icon: MapPin,
    permission: "executive.read",
    workspaces: ["/app/admin", "/app/executive"],
  },
  {
    href: "/app/executive",
    label: "Điều hành",
    icon: LayoutDashboard,
    permission: "executive.read",
    workspaces: ["/app/executive"],
  },
  {
    href: "/app/reception",
    label: "Tiếp nhận",
    icon: Building2,
    permission: "reception.read",
    workspaces: ["/app/reception"],
  },
  {
    href: "/app/doctor",
    label: "Bác sĩ",
    icon: Stethoscope,
    permission: "portal.doctor.read",
    workspaces: ["/app/doctor"],
  },
  {
    href: "/app/patient",
    label: "Bệnh nhân",
    icon: UserCircle,
    permission: "portal.patient.read",
    workspaces: ["/app/patient"],
  },
  {
    href: "/app/lab",
    label: "Phòng xét nghiệm",
    icon: FlaskConical,
    permission: "lab.read",
    workspaces: ["/app/lab"],
  },
  {
    href: "/app/collector",
    label: "Thu mẫu",
    icon: Truck,
    permission: "collections.read",
    workspaces: ["/app/collector"],
  },
  {
    href: "/app/sales",
    label: "Khách hàng (CRM)",
    icon: Users,
    workspaces: ["/app/sales"],
  },
  {
    href: "/app/clinic",
    label: "Phòng khám",
    icon: Building2,
    permission: "data.view",
    workspaces: ["/app/clinic"],
  },
];

export function buildNavItems(capabilities: AuthCapabilities | null): NavItem[] {
  if (!capabilities) return [ALL_NAV[0]];

  const workspace = capabilities.workspace;
  const adminRoles = new Set(["SUPER_ADMIN", "DXCON_ADMIN", "ADMIN", "SYSTEM_ADMIN"]);
  // user may be absent on partial capability payloads — never throw in nav.
  const isAdmin = adminRoles.has(
    (capabilities.user?.role ?? "").toUpperCase(),
  );
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
