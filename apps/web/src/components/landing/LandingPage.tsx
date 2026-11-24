import { LandingNav } from "./LandingNav";
import { HeroSection } from "./HeroSection";
import { ServicesSection } from "./ServicesSection";
import { AiSection } from "./AiSection";
import { HomeCollectionSection } from "./HomeCollectionSection";
import { PartnerSection } from "./PartnerSection";
import { PricingSection } from "./PricingSection";
import { ContactSection } from "./ContactSection";
import { LandingFooter } from "./LandingFooter";
import type { Lang } from "@/lib/landing/i18n";

export function LandingPage({ lang }: { lang: Lang }) {
  return (
    <div lang={lang} className="min-h-screen bg-slate-950">
      <LandingNav lang={lang} />
      <main>
        <HeroSection lang={lang} />
        <ServicesSection lang={lang} />
        <AiSection lang={lang} />
        <HomeCollectionSection lang={lang} />
        <PartnerSection lang={lang} />
        <PricingSection lang={lang} />
        <ContactSection lang={lang} />
      </main>
      <LandingFooter lang={lang} />
    </div>
  );
}
