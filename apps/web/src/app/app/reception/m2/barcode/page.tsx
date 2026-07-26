"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";

import { AppShell } from "@/components/layout/AppShell";
import { BarcodeWorkbench } from "@/modules/reception-m2/barcode/components/BarcodeWorkbench";

function BarcodePageInner() {
  const params = useSearchParams();
  return <BarcodeWorkbench initialOrderRef={params.get("order") ?? ""} />;
}

export default function ReceptionM2BarcodePage() {
  return (
    <AppShell title="Reception · Barcode" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Barcode labels</h1>
        <p className="text-sm text-neutral-600">
          Order, sample, and collection barcodes with standard or thermal label printing.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Loading…</p>}>
        <BarcodePageInner />
      </Suspense>
    </AppShell>
  );
}
