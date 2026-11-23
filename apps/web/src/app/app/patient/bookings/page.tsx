import Link from "next/link";

import { AppShell } from "@/components/layout/AppShell";

export const metadata = { title: "Đặt lịch lấy mẫu" };

export default function PatientBookingsPage() {
  return (
    <AppShell title="Đặt lịch lấy mẫu" workspacePath="/app/patient">
      <div className="max-w-xl space-y-4 text-sm text-slate-700">
        <p>
          Để đặt lịch lấy mẫu tại nhà, điền biểu mẫu đặt lịch. Nhân viên DxCon sẽ gọi lại để xác nhận giờ hẹn, các xét
          nghiệm và chi phí.
        </p>
        <Link
          href="/book"
          className="inline-block rounded-lg bg-teal-700 px-4 py-2 font-medium text-white hover:bg-teal-800"
        >
          Đặt lịch lấy mẫu
        </Link>
        <p className="text-slate-500">Cần hỗ trợ gấp? Liên hệ trực tiếp nơi lấy mẫu của bạn.</p>
      </div>
    </AppShell>
  );
}
