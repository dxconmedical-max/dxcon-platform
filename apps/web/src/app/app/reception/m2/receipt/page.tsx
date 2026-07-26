"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/layout/AppShell";
import { ReceiptWorkbench } from "@/modules/reception-m2/receipt/components/ReceiptWorkbench";

function ReceiptPageInner() {
  const params = useSearchParams();
  return (
    <ReceiptWorkbench
      initialOrderRef={params.get("order") ?? ""}
      initialReceiptCode={params.get("receipt") ?? ""}
    />
  );
}

export default function ReceptionM2ReceiptPage() {
  return (
    <AppShell title="Reception · Receipt" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Receipt</h1>
        <p className="text-sm text-neutral-600">
          Preview, print, thermal, PDF, re-print, and cancel cash-desk receipts.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Loading…</p>}>
        <ReceiptPageInner />
      </Suspense>
    </AppShell>
  );
}
