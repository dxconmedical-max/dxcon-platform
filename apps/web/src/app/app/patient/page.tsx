"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Kết quả của tôi",
    href: "/app/patient/results",
    description: "Tải các báo cáo xét nghiệm đã được trả.",
  },
];

export default function PatientPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Kết quả", value: "—" },
      { label: "Đơn / lượt khám", value: "—" },
      { label: "Lấy mẫu tại nhà", value: "—" },
      { label: "Tin nhắn", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Cổng bệnh nhân" workspacePath="/app/patient">
      <RoleDashboardHome
        title="Cổng bệnh nhân"
        subtitle="Kết quả đã trả và lịch sử khám của bạn (chỉ số tổng hợp, không chia sẻ thông tin cá nhân)."
        role="patient"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
