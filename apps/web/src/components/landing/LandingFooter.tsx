import Link from "next/link";

import { LANDING, type Lang } from "@/lib/landing/i18n";

export function LandingFooter({ lang }: { lang: Lang }) {
  const t = LANDING[lang];
  return (
    <footer className="border-t border-slate-800 bg-slate-950 px-4 py-10 text-slate-400 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-white font-semibold">DxCon</p>
          <p className="mt-1 text-sm">{t.footer.tagline}</p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link href="/login" className="hover:text-white">{t.nav.signIn}</Link>
          <a href={`/${lang}#pricing`} className="hover:text-white">{t.nav.pricing}</a>
          <a href={`/${lang}#contact`} className="hover:text-white">{t.nav.contact}</a>
        </div>
        <p className="text-xs">© {new Date().getFullYear()} {t.footer.company}</p>
      </div>
    </footer>
  );
}
