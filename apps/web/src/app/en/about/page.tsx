import type { Metadata } from "next";

import { AboutPage } from "@/components/landing/AboutPage";

export const metadata: Metadata = {
  title: "About us",
  description: "DxCon connects booking, sample collection, laboratories and doctors on one platform.",
  alternates: { canonical: "/en/about", languages: { vi: "/vi/about", en: "/en/about" } },
};

export default function EnAbout() {
  return <AboutPage lang="en" />;
}
