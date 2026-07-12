import Link from "next/link";
import { headers } from "next/headers";
import { ArrowRight, ClipboardCheck, Lock, Sparkles, Users } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { loginUrl } from "@/lib/urls";
import { t } from "@/lib/i18n";

export async function HeroSection() {
  const host = (await headers()).get("host");
  const signInHref = loginUrl(host);

  const capabilityCards = [
    {
      icon: ClipboardCheck,
      title: t("hero.card.orders.title"),
      text: t("hero.card.orders.text"),
    },
    {
      icon: Sparkles,
      title: t("hero.card.ai.title"),
      text: t("hero.card.ai.text"),
    },
    {
      icon: Users,
      title: t("hero.card.partners.title"),
      text: t("hero.card.partners.text"),
    },
    {
      icon: Lock,
      title: t("hero.card.security.title"),
      text: t("hero.card.security.text"),
    },
  ];

  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-16 lg:px-8 lg:pb-28 lg:pt-24">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(20,184,166,0.25),transparent_45%),radial-gradient(circle_at_bottom_left,rgba(37,99,235,0.18),transparent_40%)]" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-2">
        <div>
          <Badge tone="info" className="bg-teal-500/10 text-teal-200">
            {t("hero.badge")}
          </Badge>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
            {t("hero.title")}
          </h1>
          <p className="mt-6 max-w-xl text-lg text-slate-300">{t("hero.subtitle")}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href={signInHref}>
              <Button size="lg">
                {t("nav.signIn")}
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/contact">
              <Button size="lg" variant="outline" className="border-slate-600 text-white hover:border-teal-400">
                {t("hero.contactSales")}
              </Button>
            </Link>
          </div>
          <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-300">
            <span>{t("hero.trust.security")}</span>
            <span>{t("hero.trust.rbac")}</span>
            <span>{t("hero.trust.audit")}</span>
            <span>{t("hero.trust.ai")}</span>
          </div>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-teal-900/20 backdrop-blur">
          <p className="text-xs font-semibold uppercase tracking-wide text-teal-300">
            {t("hero.previewLabel")}
          </p>
          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            {capabilityCards.map((card) => {
              const Icon = card.icon;
              return (
                <div
                  key={card.title}
                  className="rounded-2xl border border-white/10 bg-slate-900/60 p-4"
                >
                  <Icon className="h-5 w-5 text-teal-400" />
                  <p className="mt-3 text-sm font-semibold text-white">{card.title}</p>
                  <p className="mt-1 text-xs text-slate-400">{card.text}</p>
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-sm text-slate-400">{t("hero.previewNote")}</p>
        </div>
      </div>
    </section>
  );
}
