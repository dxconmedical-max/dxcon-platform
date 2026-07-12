import type { LucideIcon } from "lucide-react";
import {
  Building2,
  CalendarPlus,
  ClipboardCheck,
  ClipboardList,
  Clock,
  FileText,
  FlaskConical,
  LayoutDashboard,
  MapPin,
  PackageCheck,
  QrCode,
  Receipt,
  Search,
  Settings,
  Sparkles,
  TestTube,
  Truck,
  UserCircle,
  UserPlus,
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
  { href: "/app/operations/logistics", label: "Live logistics", icon: Truck, permission: "executive.read", workspaces: ["/app/admin", "/app/executive", "/app/operations"] },
  { href: "/app/executive", label: "Dashboard", icon: LayoutDashboard, permission: "executive.read", workspaces: ["/app/executive"] },
  { href: "/app/reception", label: "Dashboard", icon: LayoutDashboard, permission: "reception.read", workspaces: ["/app/reception"] },
  { href: "/app/reception/queue", label: "Queue", icon: ClipboardList, permission: "reception.read", workspaces: ["/app/reception"] },
  { href: "/app/reception/register", label: "Walk-in", icon: UserPlus, permission: "reception.read", workspaces: ["/app/reception"] },
  { href: "/app/reception/search", label: "Search", icon: Search, permission: "reception.read", workspaces: ["/app/reception"] },
  { href: "/app/doctor", label: "Dashboard", icon: LayoutDashboard, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/patients", label: "Patients", icon: Users, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/orders", label: "Orders", icon: ClipboardList, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/reports", label: "Reports", icon: FileText, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/doctor/review", label: "Clinical review", icon: ClipboardCheck, permission: "portal.doctor.read", workspaces: ["/app/doctor"] },
  { href: "/app/clinic", label: "Dashboard", icon: LayoutDashboard, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/patients", label: "Patients", icon: Users, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/orders", label: "Orders", icon: ClipboardList, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/clinic/reports", label: "Reports", icon: FileText, permission: "data.view", workspaces: ["/app/clinic"] },
  { href: "/app/lab", label: "Dashboard", icon: LayoutDashboard, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/specimens", label: "Specimens", icon: TestTube, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/accession", label: "Accession", icon: PackageCheck, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/barcode", label: "Barcode", icon: QrCode, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/timeline", label: "Timeline", icon: Clock, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/samples", label: "Received Samples", icon: FlaskConical, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/queue", label: "Analyzer Queue", icon: ClipboardList, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/qc", label: "Quality Control", icon: ClipboardCheck, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/verification", label: "Verification", icon: FileText, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/cold-chain", label: "Cold chain", icon: FlaskConical, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/analyzers", label: "Analyzers", icon: FlaskConical, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/results-review", label: "Result review", icon: FileText, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/result-review", label: "Technician queue", icon: ClipboardCheck, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/lab/quarantine", label: "Quarantine", icon: ClipboardCheck, permission: "lab.read", workspaces: ["/app/lab"] },
  { href: "/app/collector", label: "Dashboard", icon: LayoutDashboard, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/collector/route", label: "Route", icon: MapPin, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/collector/trips", label: "Trips", icon: Truck, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/collector/jobs", label: "Assigned Jobs", icon: Truck, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/collector/timeline", label: "Timeline", icon: Clock, permission: "collections.read", workspaces: ["/app/collector"] },
  { href: "/app/patient", label: "Dashboard", icon: LayoutDashboard, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/book", label: "Book a test", icon: CalendarPlus, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/bookings", label: "Bookings", icon: ClipboardList, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/orders", label: "Orders", icon: ClipboardList, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/results", label: "Results", icon: FileText, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/health-summary", label: "Health Summary", icon: Sparkles, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/payments", label: "Payments", icon: Receipt, permission: "portal.patient.read", workspaces: ["/app/patient"] },
  { href: "/app/patient/profile", label: "Profile", icon: UserCircle, permission: "portal.patient.read", workspaces: ["/app/patient"] },
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
