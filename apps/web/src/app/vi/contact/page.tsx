import type { Metadata } from "next";
import Link from "next/link";

import { Faq } from "@/components/legal/Faq";
import { Fill, LegalPage } from "@/components/legal/LegalPage";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Liên hệ",
  description: "Thông tin liên hệ, giờ làm việc và hỗ trợ của DxCon.",
  alternates: { canonical: "/vi/contact" },
};

export default function ContactPage() {
  return (
    <LegalPage title="Liên hệ DxCon">
      <div className="rounded-xl border border-slate-200 p-5">
        <dl className="grid gap-3 sm:grid-cols-[10rem_1fr]">
          <dt className="font-medium text-slate-900">Đơn vị</dt>
          <dd><Fill value={SITE.legalName} /></dd>
          <dt className="font-medium text-slate-900">Mã số thuế</dt>
          <dd><Fill value={SITE.taxId} /></dd>
          <dt className="font-medium text-slate-900">Địa chỉ</dt>
          <dd><Fill value={SITE.address} /></dd>
          <dt className="font-medium text-slate-900">Điện thoại</dt>
          <dd><Fill value={SITE.phone} /></dd>
          <dt className="font-medium text-slate-900">Email</dt>
          <dd><Fill value={SITE.email} /></dd>
          <dt className="font-medium text-slate-900">Giờ làm việc</dt>
          <dd><Fill value={SITE.hours} /></dd>
        </dl>
      </div>
      <p>
        Muốn đặt lịch lấy mẫu? <Link href="/book">Đặt lịch tại đây</Link>. Phòng khám muốn hợp tác: gửi yêu cầu
        demo tại <Link href="/vi#contact">trang chủ</Link>.
      </p>
      <h2>Câu hỏi thường gặp</h2>
      <Faq />
    </LegalPage>
  );
}
