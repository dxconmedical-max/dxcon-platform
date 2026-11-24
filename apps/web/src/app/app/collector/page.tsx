"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";
import { InstallAppCard } from "@/components/pilot/InstallAppCard";

const ACTIONS = [
  {
    label: "Hàng đợi lấy mẫu",
    href: "/app/collector/queue",
    description: "Các mẫu đang chờ lấy — lọc theo khu vực, ngày, trạng thái, nhân viên.",
  },
  {
    label: "Chia sẻ vị trí của tôi",
    href: "/app/collector/location",
    description: "Bắt đầu chuyến đi để nhân viên DxCon xem bạn đang ở đâu trên bản đồ.",
  },
  {
    label: "Lấy mẫu & vận chuyển",
    href: "/app/collector/workflow",
    description: "Xác minh bệnh nhân/đơn, quét mã vạch, lấy mẫu, bàn giao, đến phòng xét nghiệm.",
  },
];

export default function CollectorPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Chờ lấy mẫu", value: "—" },
      { label: "Đang vận chuyển", value: "—" },
      { label: "Đã đến phòng XN", value: "—" },
      { label: "Từ chối / cảnh báo", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Nhân viên lấy mẫu" workspacePath="/app/collector">
      <div className="mb-4">
        <InstallAppCard />
      </div>
      <RoleDashboardHome
        title="Không gian làm việc lấy mẫu"
        subtitle="Xếp hàng, xác minh danh tính, lấy mẫu và theo dõi vận chuyển đến phòng xét nghiệm."
        role="collector"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
