"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Hộp kết quả chờ duyệt",
    href: "/app/doctor/review",
    description: "Duyệt chuyên môn: duyệt, từ chối hoặc mở lại.",
  },
  {
    label: "Bảng trả kết quả",
    href: "/app/lab/release",
    description: "Phát hành kết quả đã duyệt để bệnh nhân tải về.",
  },
];

export default function DoctorPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Chờ duyệt kết quả", value: "—" },
      { label: "Cờ nguy kịch", value: "—" },
      { label: "Báo cáo hoàn tất", value: "—" },
      { label: "Trễ hạn", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Không gian bác sĩ" workspacePath="/app/doctor">
      <RoleDashboardHome
        title="Không gian bác sĩ"
        subtitle="Duyệt kết quả chờ, cờ nguy kịch và báo cáo đã hoàn tất."
        role="doctor"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
