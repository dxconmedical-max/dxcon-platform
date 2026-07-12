import Link from "next/link";
import { headers } from "next/headers";

import { loginUrl } from "@/lib/urls";
import { t } from "@/lib/i18n";

export async function LandingFooter() {
  const host = (await headers()).get("host");
  const signInHref = loginUrl(host);

  return (
    <footer className="border-t border-slate-800 bg-slate-950 px-4 py-10 text-slate-400 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="font-semibold text-white">DxCon</p>
          <p className="mt-1 text-sm">{t("footer.tagline")}</p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link href={signInHref} className="hover:text-white">
            {t("nav.signIn")}
          </Link>
          <Link href="/pricing" className="hover:text-white">
            {t("nav.pricing")}
          </Link>
          <Link href="/contact" className="hover:text-white">
            {t("nav.contact")}
          </Link>
          <Link href="/privacy" className="hover:text-white">
            {t("footer.privacy")}
          </Link>
          <Link href="/terms" className="hover:text-white">
            {t("footer.terms")}
          </Link>
        </div>
        <p className="text-xs">© {new Date().getFullYear()} DxCon Medical</p>
      </div>
    </footer>
  );
}
