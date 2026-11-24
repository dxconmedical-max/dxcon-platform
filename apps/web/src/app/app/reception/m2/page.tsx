"use client";

import { AppShell } from "@/components/layout/AppShell";
import { ReceptionM2Placeholder } from "@/modules/reception-m2/shared/ReceptionM2Placeholder";

const DOMAINS = [
  { href: "/app/reception/m2/payment", label: "Thanh toán" },
  { href: "/app/reception/m2/receipt", label: "Biên lai" },
  { href: "/app/reception/m2/barcode", label: "Mã vạch" },
  { href: "/app/reception/m2/qr", label: "QR" },
  { href: "/app/reception/m2/lab-queue", label: "Hàng đợi xét nghiệm" },
  { href: "/app/reception/m2/sample-queue", label: "Hàng đợi mẫu" },
] as const;

export default function ReceptionM2HubPage() {
  return (
    <AppShell title="Tiếp nhận M2" workspacePath="/app/reception">
      <ReceptionM2Placeholder
        title="Trung tâm tiếp nhận"
        domain="(hub)"
        description="Trung tâm cho Thanh toán, Biên lai, Mã vạch, QR, Hàng đợi xét nghiệm và Hàng đợi mẫu."
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
