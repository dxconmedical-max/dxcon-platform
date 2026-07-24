"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Create order & documents",
    href: "/app/reception/workflow",
    description: "Patient → tests → payment → barcode/QR → requisition.",
  },
  {
    label: "Patient search",
    href: "/app/reception/search",
    description: "Search by phone, code, national ID, or name.",
  },
  {
    label: "Register patient",
    href: "/app/reception/register",
    description: "Walk-in registration with duplicate detection.",
  },
];

export default function ReceptionPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Orders today", value: "—" },
      { label: "Pending payment", value: "—" },
      { label: "Pending collection", value: "—" },
      { label: "Waiting queue", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Reception" workspacePath="/app/reception">
      <RoleDashboardHome
        title="Reception workspace"
        subtitle="Patient intake, orders, payment, barcodes/QR, and laboratory requisitions."
        role="reception"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
