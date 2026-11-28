import type { Metadata } from "next";

import { Faq, FAQ_ITEMS } from "@/components/legal/Faq";
import { LegalPage } from "@/components/legal/LegalPage";

export const metadata: Metadata = {
  title: "Câu hỏi thường gặp",
  description: "Giải đáp nhanh về đặt lịch lấy mẫu, thanh toán, kết quả và bảo mật dữ liệu tại DxCon.",
  alternates: { canonical: "/vi/faq" },
};

export default function FaqPage() {
  const ld = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: FAQ_ITEMS.map((i) => ({
      "@type": "Question",
      name: i.q,
      acceptedAnswer: { "@type": "Answer", text: i.a },
    })),
  };
  return (
    <LegalPage title="Câu hỏi thường gặp">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(ld) }} />
      <Faq />
    </LegalPage>
  );
}
