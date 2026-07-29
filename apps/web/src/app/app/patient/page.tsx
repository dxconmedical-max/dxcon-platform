"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "My results",
    href: "/app/patient/results",
    description: "Download released laboratory reports.",
  },
];

export default function PatientPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Results", value: "—" },
      { label: "Orders / visits", value: "—" },
      { label: "Home visits", value: "—" },
      { label: "Messages", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Patient portal" workspacePath="/app/patient">
      <RoleDashboardHome
        title="Patient portal"
        subtitle="Your released results and visit activity (aggregates only — no shared PII)."
        role="patient"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
