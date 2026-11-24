"use client";

import { useMemo } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { RoleDashboardHome } from "@/components/layout/RoleDashboardHome";

const ACTIONS = [
  {
    label: "Làm thêm xét nghiệm",
    href: "/app/reception/addons",
    description: "Thêm xét nghiệm trên ống mẫu đã thu (trong thời hạn cho phép).",
  },
  {
    label: "Xét nghiệm gửi ngoài",
    href: "/app/reception/sendout",
    description: "Nhắc nhập kết quả xét nghiệm gửi nước ngoài theo ngày trả dự kiến.",
  },
  {
    label: "Phiếu từ phòng khám",
    href: "/app/reception/clinic-requests",
    description: "Duyệt phiếu chỉ định do phòng khám gửi và tạo đơn 1 click.",
  },
  {
    label: "Tạo đơn xét nghiệm",
    href: "/app/reception/workflow",
    description: "Bệnh nhân → xét nghiệm → cách thu mẫu → tạo đơn.",
  },
  {
    label: "Thu mẫu tại quầy",
    href: "/app/reception/desk-collections",
    description: "Mẫu thu tại quầy: kiểm tra, thu mẫu, bàn giao cho phòng xét nghiệm.",
  },
  {
    label: "Yêu cầu thu mẫu tại nhà / phòng khám",
    href: "/app/reception/m2/field-requests",
    description: "Yêu cầu đang chờ phân công nhân viên thu mẫu.",
  },
  {
    label: "Trung tâm tiếp nhận",
    href: "/app/reception/m2",
    description: "Thanh toán, biên lai, mã vạch, QR, hàng đợi mẫu và xét nghiệm.",
  },
  {
    label: "Biên lai",
    href: "/app/reception/m2/receipt",
    description: "Xem trước, in nhiệt, PDF, in lại và hủy biên lai.",
  },
  {
    label: "Mã vạch",
    href: "/app/reception/m2/barcode",
    description: "Nhãn đơn, mẫu và thu mẫu, in bằng máy in nhiệt.",
  },
  {
    label: "Mã QR",
    href: "/app/reception/m2/qr",
    description: "QR thanh toán, VNPay, mẫu và theo dõi, có kiểm tra.",
  },
  {
    label: "Hàng đợi xét nghiệm",
    href: "/app/reception/m2/lab-queue",
    description: "Chờ → đang xử lý → hoàn tất → đã duyệt, cập nhật trực tiếp.",
  },
  {
    label: "Hàng đợi mẫu",
    href: "/app/reception/m2/sample-queue",
    description: "Đã thu → vận chuyển → nhận → phân loại → phòng xét nghiệm → hoàn tất.",
  },
  {
    label: "Yêu cầu đặt lịch",
    href: "/app/reception/bookings",
    description: "Yêu cầu từ trang đặt lịch: gọi lại, xác nhận rồi tạo đơn.",
  },
  {
    label: "Tìm bệnh nhân",
    href: "/app/reception/search",
    description: "Tìm theo số điện thoại, mã, CCCD hoặc tên.",
  },
  {
    label: "Đăng ký bệnh nhân",
    href: "/app/reception/register",
    description: "Đăng ký bệnh nhân đến trực tiếp, có kiểm tra trùng.",
  },
];

export default function ReceptionPage() {
  const fallbackCards = useMemo(
    () => [
      { label: "Đơn hôm nay", value: "—" },
      { label: "Chờ thanh toán", value: "—" },
      { label: "Chờ lấy mẫu", value: "—" },
      { label: "Hàng chờ", value: "—" },
    ],
    [],
  );

  return (
    <AppShell title="Tiếp nhận" workspacePath="/app/reception">
      <RoleDashboardHome
        title="Không gian tiếp nhận"
        subtitle="Tiếp nhận bệnh nhân, danh mục xét nghiệm, giá chuẩn và tạo đơn xét nghiệm."
        role="reception"
        fallbackCards={fallbackCards}
        actions={ACTIONS}
      />
    </AppShell>
  );
}
