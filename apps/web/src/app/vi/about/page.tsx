import type { Metadata } from "next";

import { AboutPage } from "@/components/landing/AboutPage";

export const metadata: Metadata = {
  title: "Về chúng tôi",
  description: "DxCon nối liền đặt lịch, lấy mẫu, phòng xét nghiệm và bác sĩ trên một nền tảng.",
  alternates: { canonical: "/vi/about", languages: { vi: "/vi/about", en: "/en/about" } },
};

export default function ViAbout() {
  return <AboutPage lang="vi" />;
}
