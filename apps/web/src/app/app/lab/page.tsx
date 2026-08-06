"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Lab worklist",
    href: "/app/lab/queue",
    description: "Incoming and in-process specimens.",
  },
  {
    label: "Lab workflow",
    href: "/app/lab/workflow",
    description: "Receive → accession → process → results → tech & medical validation.",
  },
  {
    label: "Release results",
    href: "/app/lab/release",
    description: "Release medically approved reports for patient download.",
  },
];

export default function LabPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Incoming", value: "—" },
      { label: "Lab queue", value: "—" },
      { label: "Pending validation", value: "—" },
      { label: "Critical / abnormal", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Laboratory" workspacePath="/app/lab">
      <RoleDashboardHome
        title="Laboratory workspace"
        subtitle="Specimen receipt, accession, processing, result entry, and validation."
        role="laboratory"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
