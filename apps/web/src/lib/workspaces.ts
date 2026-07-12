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
      { label: "Today's queue", href: "/app/reception/queue", description: "Check-in and manage the queue." },
      { label: "Walk-in registration", href: "/app/reception/register", description: "Register a new walk-in patient." },
      { label: "Search", href: "/app/reception/search", description: "Find patients and bookings." },
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
    subtitle: "LIMS specimen lifecycle, accession, QC, and result validation.",
    permission: "lab.read",
    dashboardPath: "/api/v1/lab/dashboard",
    actions: [
      { label: "Specimens", href: "/app/lab/specimens", description: "All specimens and lifecycle status." },
      { label: "Accession", href: "/app/lab/accession", description: "Receive and accession specimens." },
      { label: "Barcode viewer", href: "/app/lab/barcode", description: "View and verify specimen barcodes." },
      { label: "Status timeline", href: "/app/lab/timeline", description: "Specimen status history." },
      { label: "Analyzer queue", href: "/app/lab/queue", description: "Samples in testing." },
      { label: "Quality control", href: "/app/lab/qc", description: "QC status for runs." },
      { label: "Verification & release", href: "/app/lab/verification", description: "Verify and release results." },
    ],
    extractStatusCards: (data) => {
      const kpis = (nested(data, "kpis") ?? nested(data, "summary") ?? data) as Record<string, unknown>;
      return [
        { label: "Samples Today", value: asNumber(kpis.samples_today) },
        { label: "Pending Collection", value: asNumber(kpis.pending_collection) },
        { label: "In Transit", value: asNumber(kpis.in_transit) },
        { label: "Received", value: asNumber(kpis.received) },
        { label: "Processing", value: asNumber(kpis.processing) },
        { label: "QC Failed", value: asNumber(kpis.qc_failed) },
        { label: "Validation Pending", value: asNumber(kpis.validation_pending) },
        { label: "Released Today", value: asNumber(kpis.released_today) },
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
      { label: "Today's route", href: "/app/collector/route", description: "Route stops and navigation." },
      { label: "Assigned jobs", href: "/app/collector/jobs", description: "Today's collection assignments." },
      { label: "Timeline", href: "/app/collector/timeline", description: "Recent collection activity." },
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
      { label: "Book a service", href: "/app/patient/book", description: "Start a new booking." },
      { label: "My bookings", href: "/app/patient/bookings", description: "Scheduled collections and visits." },
      { label: "Results", href: "/app/patient/results", description: "Released test reports." },
      { label: "Health summary", href: "/app/patient/health-summary", description: "AI overview of recent results." },
      { label: "Payments", href: "/app/patient/payments", description: "Invoices and payment status." },
      { label: "Profile", href: "/app/patient/profile", description: "Personal and contact details." },
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
