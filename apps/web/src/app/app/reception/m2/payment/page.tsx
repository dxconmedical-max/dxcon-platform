"use client";

import { AppShell } from "@/components/layout/AppShell";
import { PaymentPanelPlaceholder } from "@/modules/reception-m2/payment";
import { ReceptionM2Placeholder } from "@/modules/reception-m2/shared/ReceptionM2Placeholder";

export default function ReceptionM2PaymentPage() {
  return (
    <AppShell title="Tiếp nhận · Thanh toán" workspacePath="/app/reception">
      <ReceptionM2Placeholder
        title="Thanh toán"
        domain="payment"
        description="Thu tiền theo đơn đã tạo."
      />
      <div className="mx-auto max-w-2xl">
        <PaymentPanelPlaceholder />
      </div>
    </AppShell>
  );
}
