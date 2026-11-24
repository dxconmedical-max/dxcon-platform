import type { Metadata } from "next";

import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: { absolute: "DxCon — Nền tảng xét nghiệm y khoa kết nối" },
  description:
    "DxCon kết nối phòng xét nghiệm, phòng khám, bác sĩ và bệnh nhân với quy trình xét nghiệm an toàn.",
  alternates: { canonical: "/vi", languages: { vi: "/vi", en: "/en" } },
};

export default function HomePage() {
  return <LandingPage lang="vi" />;
}
