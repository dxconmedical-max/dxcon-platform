"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Collection queue",
    href: "/app/collector/queue",
    description: "Specimens awaiting collection — filter by location, date, status, collector.",
  },
  {
    label: "Collect & transport",
    href: "/app/collector/workflow",
    description: "Verify patient/order, scan barcode, collect, dispatch, arrive at lab.",
  },
];

export default function CollectorPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Awaiting collection", value: "—" },
      { label: "In transit", value: "—" },
      { label: "Arrived at lab", value: "—" },
      { label: "Rejected / alerts", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Collector" workspacePath="/app/collector">
      <RoleDashboardHome
        title="Sample Collection workspace"
        subtitle="Queue, verify identifiers, collect specimens, and track transport to laboratory arrival."
        role="collector"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
