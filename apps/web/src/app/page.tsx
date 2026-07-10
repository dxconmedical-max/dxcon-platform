import { LandingNav } from "@/components/landing/LandingNav";
import { HeroSection } from "@/components/landing/HeroSection";
import { ServicesSection } from "@/components/landing/ServicesSection";
import { AiSection } from "@/components/landing/AiSection";
import { HomeCollectionSection } from "@/components/landing/HomeCollectionSection";
import { PartnerSection } from "@/components/landing/PartnerSection";
import { PricingSection } from "@/components/landing/PricingSection";
import { ContactSection } from "@/components/landing/ContactSection";
import { LandingFooter } from "@/components/landing/LandingFooter";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-slate-950">
      <LandingNav />
      <main>
        <HeroSection />
        <ServicesSection />
        <AiSection />
        <HomeCollectionSection />
        <PartnerSection />
        <PricingSection />
        <ContactSection />
      </main>
      <LandingFooter />
    </div>
  );
}
