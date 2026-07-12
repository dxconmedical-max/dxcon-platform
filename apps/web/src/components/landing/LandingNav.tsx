import Link from "next/link";
import { headers } from "next/headers";
import { Activity } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { bookDemoUrl, loginUrl } from "@/lib/urls";
import { t } from "@/lib/i18n";

export async function LandingNav() {
  const host = (await headers()).get("host");
  const signInHref = loginUrl(host);
  const demoHref = bookDemoUrl(host);

  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500">
            <Activity className="h-5 w-5" />
          </span>
          <span className="text-lg font-semibold">DxCon</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <Link href="/services" className="hover:text-white">
            {t("nav.services")}
          </Link>
          <Link href="/#ai" className="hover:text-white">
            {t("nav.ai")}
          </Link>
          <Link href="/solutions" className="hover:text-white">
            Solutions
          </Link>
          <Link href="/partners" className="hover:text-white">
            {t("nav.partners")}
          </Link>
          <Link href="/pricing" className="hover:text-white">
            {t("nav.pricing")}
          </Link>
          <Link href="/contact" className="hover:text-white">
            {t("nav.contact")}
          </Link>
        </nav>
        <div className="flex items-center gap-2">
          <Link href={signInHref}>
            <Button variant="ghost" className="text-slate-200 hover:bg-white/10 hover:text-white">
              {t("nav.signIn")}
            </Button>
          </Link>
          <Link href={demoHref}>
            <Button>{t("nav.bookDemo")}</Button>
          </Link>
        </div>
      </div>
    </header>
  );
}
