"use client";

import { AppShell } from "@/components/layout/AppShell";
import { SampleQueueWorkbench } from "@/modules/reception-m2/sample-queue/components/SampleQueueWorkbench";

export default function ReceptionM2SampleQueuePage() {
  return (
    <AppShell title="Reception · Sample Queue" workspacePath="/app/reception">
      <div className="mx-auto max-w-6xl space-y-2 px-4 pt-4">
        <h1 className="text-2xl font-semibold">Sample queue</h1>
        <p className="text-sm text-neutral-600">
          Collected → transport → received → sorting → laboratory → completed, with live tracking
          and history.
        </p>
      </div>
      <SampleQueueWorkbench />
    </AppShell>
  );
}
