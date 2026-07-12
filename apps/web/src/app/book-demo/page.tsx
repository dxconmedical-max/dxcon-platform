import Link from "next/link";
import { Mail } from "lucide-react";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { t } from "@/lib/i18n";

export const metadata = { title: "Book demo" };

export default function BookDemoPage() {
  return (
    <MarketingPageShell>
      <section className="bg-slate-50 px-4 py-20 lg:px-8">
        <div className="mx-auto max-w-2xl">
          <Link href="/" className="text-sm text-teal-700 hover:text-teal-800">
            ← Back to home
          </Link>
          <h1 className="mt-6 text-3xl font-semibold text-slate-900">{t("bookDemo.title")}</h1>
          <p className="mt-3 text-slate-600">{t("bookDemo.subtitle")}</p>
          <form
            className="mt-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            action="mailto:sales@dxcon.com.vn"
            method="post"
            encType="text/plain"
          >
            <div>
              <Label htmlFor="demo-name">Name</Label>
              <Input id="demo-name" name="name" required placeholder="Your name" />
            </div>
            <div>
              <Label htmlFor="demo-org">Organization</Label>
              <Input id="demo-org" name="organization" required placeholder="Clinic / Lab" />
            </div>
            <div>
              <Label htmlFor="demo-email">Work email</Label>
              <Input id="demo-email" name="email" type="email" required placeholder="you@company.com" />
            </div>
            <div>
              <Label htmlFor="demo-notes">Use case</Label>
              <textarea
                id="demo-notes"
                name="notes"
                rows={4}
                required
                placeholder="Sites, volume, integrations"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
              />
            </div>
            <Button type="submit" className="w-full">
              {t("bookDemo.submit")}
            </Button>
            <p className="flex items-center justify-center gap-2 text-xs text-slate-500">
              <Mail className="h-3 w-3" />
              Or email sales@dxcon.com.vn directly
            </p>
          </form>
        </div>
      </section>
    </MarketingPageShell>
  );
}
