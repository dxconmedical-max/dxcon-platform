"use client";

import { AppShell } from "@/components/layout/AppShell";
import { LabQueueWorkbench } from "@/modules/reception-m2/lab-queue/components/LabQueueWorkbench";

export default function ReceptionM2LabQueuePage() {
  return (
    <AppShell title="Tiếp nhận · Hàng đợi xét nghiệm" workspacePath="/app/reception">
      <div className="mx-auto max-w-6xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Hàng đợi xét nghiệm</h1>
        <p className="text-sm text-neutral-600">
          Đã thanh toán → mã vạch → hàng đợi → chờ → xử lý → hoàn tất → đã duyệt.
        </p>
      </div>
      <LabQueueWorkbench />
    </AppShell>
  );
}
