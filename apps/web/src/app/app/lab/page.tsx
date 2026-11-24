"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Danh sách việc phòng xét nghiệm",
    href: "/app/lab/queue",
    description: "Mẫu đang đến và đang xử lý.",
  },
  {
    label: "Quy trình xét nghiệm",
    href: "/app/lab/workflow",
    description: "Nhận mẫu → mã số mẫu → xử lý → kết quả → duyệt kỹ thuật và duyệt chuyên môn.",
  },
  {
    label: "Trả kết quả",
    href: "/app/lab/release",
    description: "Phát hành báo cáo đã được bác sĩ duyệt để bệnh nhân tải về.",
  },
];

export default function LabPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Mẫu đến", value: "—" },
      { label: "Hàng đợi xét nghiệm", value: "—" },
      { label: "Chờ duyệt", value: "—" },
      { label: "Nguy kịch / bất thường", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Phòng xét nghiệm" workspacePath="/app/lab">
      <RoleDashboardHome
        title="Không gian phòng xét nghiệm"
        subtitle="Nhận mẫu, cấp mã số, xử lý, nhập kết quả và duyệt."
        role="laboratory"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
