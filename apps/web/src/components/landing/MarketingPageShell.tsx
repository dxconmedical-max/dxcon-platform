import type { ReactNode } from "react";

import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingNav } from "@/components/landing/LandingNav";

export function MarketingPageShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-slate-950">
      <LandingNav />
      <main>{children}</main>
      <LandingFooter />
    </div>
  );
}
