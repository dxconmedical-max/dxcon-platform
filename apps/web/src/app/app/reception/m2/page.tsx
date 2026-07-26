"use client";

import { AppShell } from "@/components/layout/AppShell";
import { ReceptionM2Placeholder } from "@/modules/reception-m2/shared/ReceptionM2Placeholder";

const DOMAINS = [
  { href: "/app/reception/m2/payment", label: "Payment" },
  { href: "/app/reception/m2/receipt", label: "Receipt" },
  { href: "/app/reception/m2/barcode", label: "Barcode" },
  { href: "/app/reception/m2/qr", label: "QR" },
  { href: "/app/reception/m2/lab-queue", label: "Lab Queue" },
  { href: "/app/reception/m2/sample-queue", label: "Sample Queue" },
] as const;

export default function ReceptionM2HubPage() {
  return (
    <AppShell title="Reception M2" workspacePath="/app/reception">
      <ReceptionM2Placeholder
        title="Reception Milestone 2"
        domain="(hub)"
        description="Architecture hub for Payment, Receipt, Barcode, QR, Lab Queue, and Sample Queue. No business logic on this foundation pass."
      />
      <ul className="mx-auto mt-6 max-w-2xl space-y-2 text-sm">
        {DOMAINS.map((d) => (
          <li key={d.href}>
            <a className="text-sky-700 underline" href={d.href}>
              {d.label}
            </a>
          </li>
        ))}
      </ul>
    </AppShell>
  );
}
