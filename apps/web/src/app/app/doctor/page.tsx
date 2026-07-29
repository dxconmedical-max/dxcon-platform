"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Result inbox",
    href: "/app/doctor/review",
    description: "Medical validation: approve, reject, or reopen.",
  },
  {
    label: "Release board",
    href: "/app/lab/release",
    description: "Release approved results for patient download.",
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
