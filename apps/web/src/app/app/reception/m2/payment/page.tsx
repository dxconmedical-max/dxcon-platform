"use client";

import { AppShell } from "@/components/layout/AppShell";
import { PaymentPanelPlaceholder } from "@/modules/reception-m2/payment";
import { ReceptionM2Placeholder } from "@/modules/reception-m2/shared/ReceptionM2Placeholder";

export default function ReceptionM2PaymentPage() {
  return (
    <AppShell title="Reception · Payment" workspacePath="/app/reception">
      <ReceptionM2Placeholder
        title="Payment"
        domain="payment"
        description="Collect payment against M1 orders. UI logic not implemented in foundation."
      />
      <div className="mx-auto max-w-2xl">
        <PaymentPanelPlaceholder />
      </div>
    </AppShell>
  );
}
