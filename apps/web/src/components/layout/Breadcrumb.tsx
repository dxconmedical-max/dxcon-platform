"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LABELS: Record<string, string> = {
  app: "Trang làm việc",
  admin: "Quản trị",
  executive: "Điều hành",
  reception: "Tiếp nhận",
  doctor: "Bác sĩ",
  patient: "Bệnh nhân",
  lab: "Phòng xét nghiệm",
  collector: "Thu mẫu",
  clinic: "Phòng khám",
  sales: "Kinh doanh",
  operations: "Vận hành",
  support: "Hỗ trợ",
  "clinic-results": "Kết quả phòng khám",
  "clinic-billing": "Bảng giá phòng khám",
  "clinic-settings": "Cài đặt phòng khám",
  "lab-payables": "Công nợ phòng xét nghiệm",
  profit: "Báo cáo lãi",
  bookings: "Yêu cầu đặt lịch",
  "new-request": "Gửi phiếu chỉ định",
  "clinic-requests": "Phiếu chỉ định",
  users: "Người dùng",
  "test-catalog": "Danh mục xét nghiệm",
  workflow: "Tiếp nhận đơn",
  queue: "Hàng đợi",
  orders: "Đơn hàng",
  patients: "Bệnh nhân",
  results: "Kết quả",
  settings: "Cài đặt",
  billing: "Thanh toán",
  reports: "Báo cáo",
  customers: "Khách hàng",
  "demo-requests": "Yêu cầu demo",
  integrations: "Tích hợp",
  organizations: "Đơn vị",
  "reference-ranges": "Khoảng tham chiếu",
  reporting: "Báo cáo tổng hợp",
  "test-flags": "Cờ xét nghiệm",
};

export function Breadcrumb() {
  const pathname = usePathname();
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) {
    return null;
  }

  const crumbs = segments.map((segment, index) => {
    const href = `/${segments.slice(0, index + 1).join("/")}`;
    const label = LABELS[segment] ?? segment;
    return { href, label, last: index === segments.length - 1 };
  });

  return (
    <nav aria-label="Breadcrumb" className="mt-0.5 flex items-center gap-1 text-xs text-slate-500">
      {crumbs.map((crumb) =>
        crumb.last ? (
          <span key={crumb.href} className="font-medium text-slate-700">
            {crumb.label}
          </span>
        ) : (
          <span key={crumb.href} className="flex items-center gap-1">
            <Link href={crumb.href} className="hover:text-teal-700">
              {crumb.label}
            </Link>
            <span>/</span>
          </span>
        ),
      )}
    </nav>
  );
}
