"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  { label: "Organizations", href: "/app/admin/organizations", description: "Tenant onboarding and setup." },
  { label: "Staff accounts", href: "/app/admin/users", description: "Create and disable staff logins." },
  { label: "Customer onboarding", href: "/app/admin/onboarding", description: "Wizard for new customers." },
  { label: "Demo requests", href: "/app/admin/demo-requests", description: "Yêu cầu demo gửi từ website: liên hệ lại và đổi trạng thái." },
  { label: "Integrations", href: "/app/admin/integrations", description: "Connectors and webhooks." },
  { label: "Reference ranges", href: "/app/admin/reference-ranges", description: "Upload lab reference ranges as a draft, review, then activate." },
  { label: "Test catalog import", href: "/app/admin/test-catalog", description: "Upload the test list and prices (CSV), preview, apply." },
  { label: "Operations", href: "/app/operations", description: "Production health and ops dashboard." },
];

export default function AdminPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Orders today", value: "—" },
      { label: "Pending collection", value: "—" },
      { label: "Lab queue", value: "—" },
      { label: "Ops alerts", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Administration" workspacePath="/app/admin">
      <RoleDashboardHome
        title="Admin workspace"
        subtitle="Operational KPIs across orders, collection, lab queue, TAT, and alerts."
        role="admin"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
