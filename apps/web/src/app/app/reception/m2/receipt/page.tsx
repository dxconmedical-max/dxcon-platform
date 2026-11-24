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
    <AppShell title="Tiếp nhận · Biên lai" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Biên lai</h1>
        <p className="text-sm text-neutral-600">
          Xem trước, in, in nhiệt, PDF, in lại và hủy biên lai thu tiền.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Đang tải…</p>}>
        <ReceiptPageInner />
      </Suspense>
    </AppShell>
  );
}
