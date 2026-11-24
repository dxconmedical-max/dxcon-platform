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
    <AppShell title="Tiếp nhận · Mã vạch" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Nhãn mã vạch</h1>
        <p className="text-sm text-neutral-600">
          Mã vạch đơn, mẫu và thu mẫu, in nhãn thường hoặc nhãn nhiệt.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Đang tải…</p>}>
        <BarcodePageInner />
      </Suspense>
    </AppShell>
  );
}
