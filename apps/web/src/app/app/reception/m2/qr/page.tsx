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
    <AppShell title="Tiếp nhận · Mã QR" workspacePath="/app/reception">
      <div className="mx-auto max-w-4xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Mã QR</h1>
        <p className="text-sm text-neutral-600">
          QR thanh toán, VNPay, tĩnh, động, mẫu và theo dõi, có kiểm tra nội dung.
        </p>
      </div>
      <Suspense fallback={<p className="p-4 text-sm">Đang tải…</p>}>
        <QrPageInner />
      </Suspense>
    </AppShell>
  );
}
