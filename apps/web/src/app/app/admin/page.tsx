"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  { label: "Organizations", href: "/app/admin/organizations", description: "Tenant onboarding and setup." },
  { label: "Customer onboarding", href: "/app/admin/onboarding", description: "Wizard for new customers." },
  { label: "Integrations", href: "/app/admin/integrations", description: "Connectors and webhooks." },
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
