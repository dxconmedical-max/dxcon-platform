import Link from "next/link";
import { Activity } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { LANDING, type Lang } from "@/lib/landing/i18n";

export function LandingNav({ lang, path = "" }: { lang: Lang; path?: string }) {
  const t = LANDING[lang].nav;
  const other: Lang = lang === "vi" ? "en" : "vi";
  const other_href = `/${other}${path}`;
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        <Link href={`/${lang}`} className="flex items-center gap-2 text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500">
            <Activity className="h-5 w-5" />
          </span>
          <span className="text-lg font-semibold">DxCon</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <Link href={`/${lang}/about`} className="hover:text-white">{t.about}</Link>
          <a href={`/${lang}#services`} className="hover:text-white">{t.services}</a>
          <a href={`/${lang}#ai`} className="hover:text-white">{t.ai}</a>
          <a href={`/${lang}#partners`} className="hover:text-white">{t.partners}</a>
          <a href={`/${lang}#pricing`} className="hover:text-white">{t.pricing}</a>
          <a href={`/${lang}#contact`} className="hover:text-white">{t.contact}</a>
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href={other_href}
            hrefLang={other}
            aria-label={other === "en" ? "Switch to English" : "Chuyển sang Tiếng Việt"}
            className="rounded-lg border border-white/20 px-2.5 py-1.5 text-xs font-semibold text-slate-200 hover:bg-white/10"
          >
            <span className={lang === "vi" ? "text-teal-300" : "text-slate-400"}>VI</span>
            <span className="px-1 text-slate-500">|</span>
            <span className={lang === "en" ? "text-teal-300" : "text-slate-400"}>EN</span>
          </Link>
          <Link href="/login" className="hidden sm:block">
            <Button variant="ghost" className="text-slate-200 hover:bg-white/10 hover:text-white">
              {t.signIn}
            </Button>
          </Link>
          <a href={`/${lang}#contact`}>
            <Button>{t.demo}</Button>
          </a>
        </div>
      </div>
    </header>
  );
}
