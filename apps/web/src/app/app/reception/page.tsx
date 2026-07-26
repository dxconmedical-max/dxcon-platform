"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Create laboratory order",
    href: "/app/reception/workflow",
    description: "Patient → tests → review pricing → create order (Milestone 1).",
  },
  {
    label: "Reception M2 foundation",
    href: "/app/reception/m2",
    description: "Architecture hub: payment, receipt, barcode, QR, lab/sample queues (no logic yet).",
  },
  {
    label: "Receipts",
    href: "/app/reception/m2/receipt",
    description: "Preview, print, thermal, PDF, re-print, and cancel receipts.",
  },
  {
    label: "Barcodes",
    href: "/app/reception/m2/barcode",
    description: "Order, sample, and collection labels with thermal printing.",
  },
  {
    label: "QR codes",
    href: "/app/reception/m2/qr",
    description: "Payment, VNPay, static/dynamic, sample, and tracking QR with verify.",
  },
  {
    label: "Lab queue",
    href: "/app/reception/m2/lab-queue",
    description: "Waiting → processing → completed → verified with live refresh.",
  },
  {
    label: "Sample queue",
    href: "/app/reception/m2/sample-queue",
    description: "Collected → transport → received → sorting → lab → completed.",
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
        subtitle="Patient intake, test catalog, authoritative pricing, and laboratory order creation."
        role="reception"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
