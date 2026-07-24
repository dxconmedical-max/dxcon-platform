"use client";

import Link from "next/link";
import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

import { SectionHeader } from "./_components/ui";

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

const PHASE1_JOURNEY = [
  {
    step: 1,
    title: "Find or register patient",
    href: "/app/reception/search",
    detail: "Search production patients, or open registration for walk-ins.",
  },
  {
    step: 2,
    title: "Select tests & create order",
    href: "/app/reception/workflow",
    detail: "Catalog pricing from the backend; order number issued on create.",
  },
  {
    step: 3,
    title: "Collect payment",
    href: "/app/reception/workflow",
    detail: "Full settlement unlocks barcodes, QR, and requisition print.",
  },
  {
    step: 4,
    title: "Print barcode & order form",
    href: "/app/reception/workflow",
    detail: "Stable specimen labels and laboratory requisition from paid orders.",
  },
] as const;

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
      <div className="space-y-6">
        <RoleDashboardHome
          title="Reception workspace"
          subtitle="Phase 1 — patient intake, laboratory orders, payment, barcodes, and print-ready requisitions."
          role="reception"
          fallbackCards={fallbackCards}
          actions={ACTIONS}
        />

        <Card className="space-y-4 p-5">
          <SectionHeader
            title="Phase 1 journey"
            description="Production path from patient identity through printable laboratory documents."
            actions={
              <Link href="/app/reception/workflow">
                <Button size="sm">Start order workflow</Button>
              </Link>
            }
          />
          <ol className="grid gap-3 md:grid-cols-2">
            {PHASE1_JOURNEY.map((item) => (
              <li
                key={item.step}
                className="rounded-xl border border-slate-200 bg-slate-50/80 p-4"
              >
                <div className="mb-2 flex items-center gap-2">
                  <Badge tone="info">{item.step}</Badge>
                  <p className="font-medium text-slate-900">{item.title}</p>
                </div>
                <p className="text-sm text-slate-600">{item.detail}</p>
                <Link
                  href={item.href}
                  className="mt-3 inline-flex text-sm font-medium text-sky-700 hover:text-sky-900"
                >
                  Open →
                </Link>
              </li>
            ))}
          </ol>
        </Card>
      </div>
    </AppShell>
  );
}
