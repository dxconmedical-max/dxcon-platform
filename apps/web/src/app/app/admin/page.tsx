"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  { label: "Tổ chức", href: "/app/admin/organizations", description: "Tạo và cấu hình tổ chức, phòng khám đối tác." },
  { label: "Tài khoản nhân viên", href: "/app/admin/users", description: "Tạo và khóa tài khoản đăng nhập của nhân viên." },
  { label: "Đưa khách hàng mới vào hệ thống", href: "/app/admin/onboarding", description: "Hướng dẫn từng bước khi có khách hàng mới." },
  { label: "Phòng khám tự chỉ định", href: "/app/admin/clinic-settings", description: "Bật hoặc tắt quyền tự chỉ định cho từng phòng khám." },
  { label: "Gửi ngoài & thời hạn làm thêm", href: "/app/admin/test-flags", description: "Đánh dấu xét nghiệm gửi ngoài, số ngày trả dự kiến, thời hạn làm thêm." },
  { label: "Hợp đồng & công nợ phòng khám", href: "/app/admin/clinic-billing", description: "Lưu hợp đồng, giá riêng từng phòng khám, kết toán theo kỳ và công nợ." },
  { label: "Báo cáo lãi", href: "/app/admin/profit", description: "Lãi của DxCon theo phòng khám, phòng xét nghiệm và tháng." },
  { label: "Giá nhập & công nợ phải trả phòng xét nghiệm", href: "/app/admin/lab-payables", description: "Giá nhập từ phòng xét nghiệm, gán ca, lãi của DxCon và số tiền phải trả." },
  { label: "Yêu cầu demo", href: "/app/admin/demo-requests", description: "Yêu cầu demo gửi từ website: liên hệ lại và đổi trạng thái." },
  { label: "Tích hợp", href: "/app/admin/integrations", description: "Kết nối với hệ thống bên ngoài." },
  { label: "Khoảng tham chiếu", href: "/app/admin/reference-ranges", description: "Tải khoảng tham chiếu lên dạng nháp, kiểm tra rồi kích hoạt." },
  { label: "Nhập danh mục xét nghiệm", href: "/app/admin/test-catalog", description: "Tải danh sách xét nghiệm và giá (CSV), xem trước rồi áp dụng." },
  { label: "Báo cáo", href: "/app/admin/reporting", description: "Báo cáo đơn hàng và doanh thu theo ngày." },
  { label: "Vận hành", href: "/app/operations", description: "Tình trạng hệ thống và bảng điều khiển vận hành." },
];

export default function AdminPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Đơn hôm nay", value: "—" },
      { label: "Chờ lấy mẫu", value: "—" },
      { label: "Hàng đợi xét nghiệm", value: "—" },
      { label: "Cảnh báo vận hành", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Quản trị" workspacePath="/app/admin">
      <RoleDashboardHome
        title="Không gian quản trị"
        subtitle="Chỉ số vận hành: đơn hàng, thu mẫu, hàng đợi xét nghiệm, TAT và cảnh báo."
        role="admin"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
