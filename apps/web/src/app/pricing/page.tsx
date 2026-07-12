import Link from "next/link";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";
import { PricingSection } from "@/components/landing/PricingSection";

export const metadata = { title: "Pricing" };

export default function PricingPage() {
  return (
    <MarketingPageShell>
      <div className="px-4 pt-12 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <Link href="/" className="text-sm text-teal-400 hover:text-teal-300">
            ← Back to home
          </Link>
        </div>
      </div>
      <PricingSection />
    </MarketingPageShell>
  );
}
