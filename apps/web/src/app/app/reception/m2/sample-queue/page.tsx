"use client";

import { AppShell } from "@/components/layout/AppShell";
import { SampleQueueWorkbench } from "@/modules/reception-m2/sample-queue/components/SampleQueueWorkbench";

export default function ReceptionM2SampleQueuePage() {
  return (
    <AppShell title="Tiếp nhận · Hàng đợi mẫu" workspacePath="/app/reception">
      <div className="mx-auto max-w-6xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Hàng đợi mẫu</h1>
        <p className="text-sm text-neutral-600">
          Đã thu → vận chuyển → đã nhận → phân loại → phòng xét nghiệm → hoàn tất, có theo dõi trực tiếp
          and history.
        </p>
      </div>
      <SampleQueueWorkbench />
    </AppShell>
  );
}
