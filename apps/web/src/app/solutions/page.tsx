import Link from "next/link";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";
import { AiSection } from "@/components/landing/AiSection";
import { ServicesSection } from "@/components/landing/ServicesSection";

export const metadata = { title: "Solutions" };

export default function SolutionsPage() {
  return (
    <MarketingPageShell>
      <div className="px-4 pt-12 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/" className="text-sm text-teal-400 hover:text-teal-300">
            ← Back to home
          </Link>
          <h1 className="mt-6 text-3xl font-semibold text-white">DxCon solutions</h1>
          <p className="mt-3 max-w-2xl text-slate-300">
            Multi-organization diagnostics platform for laboratories, clinics, hospital groups,
            and patient engagement — with role-based access and audit-ready workflows.
          </p>
        </div>
      </div>
      <ServicesSection />
      <AiSection />
    </MarketingPageShell>
  );
}
