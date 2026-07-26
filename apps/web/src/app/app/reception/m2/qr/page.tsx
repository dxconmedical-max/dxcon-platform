"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/layout/AppShell";
import { QrWorkbench } from "@/modules/reception-m2/qr/components/QrWorkbench";

function QrPageInner() {
  const params = useSearchParams();
  return <QrWorkbench initialOrderRef={params.get("order") ?? ""} />;
}

export default function ReceptionM2QrPage() {
  return (
    <AppShell title="Reception · QR" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">QR codes</h1>
        <p className="text-sm text-neutral-600">
          Payment, VNPay, static, dynamic, sample, and tracking QR with payload verification.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Loading…</p>}>
        <QrPageInner />
      </Suspense>
    </AppShell>
  );
}
