import Link from "next/link";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";
import { ServicesSection } from "@/components/landing/ServicesSection";

export const metadata = { title: "Services" };

export default function ServicesPage() {
  return (
    <MarketingPageShell>
      <div className="px-4 pt-12 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/" className="text-sm text-teal-400 hover:text-teal-300">
            ← Back to home
          </Link>
        </div>
      </div>
      <ServicesSection />
    </MarketingPageShell>
  );
}
