"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Result inbox",
    href: "/app/doctor",
    description: "Pending medical validation and critical flags (aggregate metrics live).",
  },
];

export default function DoctorPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Pending reviews", value: "—" },
      { label: "Critical flags", value: "—" },
      { label: "Completed reports", value: "—" },
      { label: "Overdue", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Doctor workspace" workspacePath="/app/doctor">
      <RoleDashboardHome
        title="Doctor workspace"
        subtitle="Review pending results, critical flags, and completed reports."
        role="doctor"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
