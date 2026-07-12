import type { StatusCard } from "@/components/layout/WorkspaceHome";

export type WorkspaceAction = {
  label: string;
  href: string;
  description?: string;
  comingSoon?: boolean;
};

export type WorkspaceKey =
  | "admin"
  | "executive"
  | "reception"
  | "doctor"
  | "lab"
  | "collector"
  | "clinic"
  | "patient";

export type WorkspaceDefinition = {
  key: WorkspaceKey;
  path: string;
  title: string;
  subtitle: string;
  permission?: string;
  dashboardPath: string;
  actions: WorkspaceAction[];
  extractStatusCards: (data: Record<string, unknown>) => StatusCard[];
};

function asNumber(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return Number.isFinite(value) ? String(value) : "—";
  if (typeof value === "string" && value.trim() !== "") return value;
  return "—";
}

function nested(
  data: Record<string, unknown>,
  ...keys: string[]
): unknown {
  let current: unknown = data;
  for (const key of keys) {
    if (!current || typeof current !== "object") return undefined;
    current = (current as Record<string, unknown>)[key];
  }
  return current;
}

export const WORKSPACE_DEFINITIONS: Record<WorkspaceKey, WorkspaceDefinition> = {
  admin: {
    key: "admin",
    path: "/app/admin",
    title: "Administration",
    subtitle: "Manage users, tenants, integrations, and platform configuration.",
    permission: "users.read",
    dashboardPath: "/api/v1/dashboard/admin",
    actions: [
      { label: "Organizations", href: "/app/admin/organizations", description: "Tenant onboarding and setup." },
      { label: "Patients", href: "/app/admin/patients", description: "Organization patient registry." },
      { label: "Orders", href: "/app/admin/orders", description: "Order registry." },
      { label: "Customer onboarding", href: "/app/admin/onboarding", description: "Wizard for new customers." },
      { label: "Integrations", href: "/app/admin/integrations", description: "Connectors and webhooks." },
      { label: "Operations", href: "/app/operations", description: "Production health and ops dashboard." },
    ],
    extractStatusCards: (data) => {
      const summary = (nested(data, "summary") ?? data) as Record<string, unknown>;
      return [
        { label: "Users", value: asNumber(summary.users ?? summary.total_users) },
        { label: "Organizations", value: asNumber(summary.organizations ?? summary.tenants) },
        { label: "Orders", value: asNumber(summary.orders) },
        { label: "Revenue", value: asNumber(summary.revenue) },
      ];
    },
  },
  executive: {
    key: "executive",
    path: "/app/executive",
    title: "Executive",
    subtitle: "Organization KPIs, finance, and operational oversight.",
    permission: "executive.read",
    dashboardPath: "/api/v1/executive-platform/dashboard",
    actions: [
      { label: "Operations center", href: "/app/operations", description: "Pilot readiness and health." },
    ],
    extractStatusCards: (data) => {
      const widgets = (nested(data, "widgets") ?? nested(data, "kpis") ?? data) as Record<string, unknown>;
      return [
        { label: "Revenue", value: asNumber(widgets.revenue ?? widgets.total_revenue) },
        { label: "Orders", value: asNumber(widgets.orders ?? widgets.total_orders) },
        { label: "Partners", value: asNumber(widgets.partners ?? widgets.active_partners) },
        { label: "SLA", value: asNumber(widgets.sla_score ?? widgets.sla) },
      ];
    },
  },
  reception: {
    key: "reception",
    path: "/app/reception",
    title: "Reception",
    subtitle: "Patient check-in, orders, payments, and queue management.",
    permission: "reception.read",
    dashboardPath: "/api/v1/reception/workspace/dashboard",
    actions: [
      { label: "Patient queue", href: "/app/reception", description: "Today's reception queue." },
    ],
    extractStatusCards: (data) => {
      const kpis = (nested(data, "kpis") ?? data) as Record<string, unknown>;
      return [
        { label: "Queue waiting", value: asNumber(kpis.waiting ?? kpis.queue_waiting) },
        { label: "Checked in", value: asNumber(kpis.checked_in) },
        { label: "Pending payments", value: asNumber(kpis.pending_payments ?? kpis.pending_payment) },
        { label: "Collections", value: asNumber(kpis.waiting_collections) },
      ];
    },
  },
  doctor: {
    key: "doctor",
    path: "/app/doctor",
    title: "Doctor",
    subtitle: "Review results, manage patients, and clinical workflows.",
    permission: "portal.doctor.read",
    dashboardPath: "/api/v1/portal/doctor/dashboard",
    actions: [
      { label: "Patients", href: "/app/doctor/patients", description: "Assigned patients." },
      { label: "Reports", href: "/app/doctor/reports", description: "Pending clinical reviews." },
      { label: "Orders", href: "/app/doctor/orders", description: "Clinical orders." },
    ],
    extractStatusCards: (data) => {
      const widgets = (nested(data, "widgets") ?? data) as Record<string, unknown>;
      return [
        { label: "Pending reviews", value: asNumber(widgets.pending_reviews) },
        { label: "Patients", value: asNumber(widgets.todays_patients ?? widgets.assigned_patients) },
        { label: "Critical flags", value: asNumber(widgets.critical_results) },
        { label: "Notifications", value: asNumber(widgets.notifications) },
      ];
    },
  },
  lab: {
    key: "lab",
    path: "/app/lab",
    title: "Laboratory",
    subtitle: "Accessions, testing queue, QC, and result validation.",
    permission: "lab.read",
    dashboardPath: "/api/v1/lab/workspace/dashboard",
    actions: [
      { label: "Work queue", href: "/app/lab/samples", description: "Samples in testing." },
    ],
    extractStatusCards: (data) => {
      const kpis = (nested(data, "kpis") ?? nested(data, "summary") ?? data) as Record<string, unknown>;
      return [
        { label: "Pending accessions", value: asNumber(kpis.pending_accessions ?? kpis.pending) },
        { label: "In testing", value: asNumber(kpis.in_testing ?? kpis.testing) },
        { label: "QC pending", value: asNumber(kpis.qc_pending) },
        { label: "Released today", value: asNumber(kpis.released_today ?? kpis.completed) },
      ];
    },
  },
  collector: {
    key: "collector",
    path: "/app/collector",
    title: "Collector",
    subtitle: "Home collection routes, assignments, and sample handoff.",
    permission: "collections.read",
    dashboardPath: "/api/v1/dashboard/collector",
    actions: [
      { label: "Assigned jobs", href: "/app/collector/jobs", description: "Today's collection assignments." },
    ],
    extractStatusCards: (data) => {
      const summary = (nested(data, "summary") ?? nested(data, "kpis") ?? data) as Record<string, unknown>;
      return [
        { label: "Assigned", value: asNumber(summary.assigned ?? summary.total_assigned) },
        { label: "Completed", value: asNumber(summary.completed) },
        { label: "In progress", value: asNumber(summary.in_progress) },
        { label: "Exceptions", value: asNumber(summary.exceptions ?? summary.failed) },
      ];
    },
  },
  clinic: {
    key: "clinic",
    path: "/app/clinic",
    title: "Clinic",
    subtitle: "Bookings, orders, and clinic operations.",
    permission: "data.view",
    dashboardPath: "/api/v1/clinic/dashboard",
    actions: [
      { label: "Patients", href: "/app/clinic/patients", description: "Clinic patient registry." },
      { label: "Orders", href: "/app/clinic/orders", description: "Clinic orders." },
      { label: "Reports", href: "/app/clinic/reports", description: "Clinic reports." },
    ],
    extractStatusCards: (data) => {
      const summary = (nested(data, "summary") ?? nested(data, "kpis") ?? data) as Record<string, unknown>;
      return [
        { label: "Bookings today", value: asNumber(summary.bookings_today ?? summary.today_bookings) },
        { label: "Orders", value: asNumber(summary.orders) },
        { label: "Patients", value: asNumber(summary.patients) },
        { label: "Revenue", value: asNumber(summary.revenue) },
      ];
    },
  },
  patient: {
    key: "patient",
    path: "/app/patient",
    title: "Patient",
    subtitle: "Results, bookings, invoices, and health records.",
    permission: "portal.patient.read",
    dashboardPath: "/api/v1/portal/patient/dashboard",
    actions: [
      { label: "My bookings", href: "/app/patient/bookings", description: "Scheduled collections and visits." },
      { label: "Payments", href: "/app/patient/payments", description: "Invoices and payment status." },
    ],
    extractStatusCards: (data) => {
      const summary = (nested(data, "summary") ?? nested(data, "widgets") ?? data) as Record<string, unknown>;
      return [
        { label: "Open orders", value: asNumber(summary.open_orders ?? summary.orders) },
        { label: "Reports", value: asNumber(summary.released_reports ?? summary.reports) },
        { label: "Outstanding", value: asNumber(summary.outstanding_balance ?? summary.outstanding) },
        { label: "Notifications", value: asNumber(summary.notifications) },
      ];
    },
  },
};

export function workspaceByPath(path: string): WorkspaceDefinition | undefined {
  return Object.values(WORKSPACE_DEFINITIONS).find((ws) => ws.path === path);
}

export function workspaceByKey(key: WorkspaceKey): WorkspaceDefinition {
  return WORKSPACE_DEFINITIONS[key];
}
