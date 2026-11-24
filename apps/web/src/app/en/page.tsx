import type { Metadata } from "next";

import { LandingPage } from "@/components/landing/LandingPage";

export const metadata: Metadata = {
  title: { absolute: "DxCon — Connected Diagnostics Platform" },
  description:
    "DxCon connects laboratories, clinics, doctors, and patients with secure diagnostics workflows.",
  alternates: { canonical: "/en", languages: { vi: "/vi", en: "/en" } },
};

export default function EnPage() {
  return <LandingPage lang="en" />;
}
