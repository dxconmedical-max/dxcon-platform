import { Mail, MapPin, Phone } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { LANDING, type Lang } from "@/lib/landing/i18n";
import { Input, Label } from "@/components/ui/Input";

export function ContactSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].contact;
  return (
    <section id="contact" className="bg-slate-50 px-4 py-20 lg:px-8">
      <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-2">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            {t.eyebrow}
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">
            {t.title}
          </h2>
          <p className="mt-4 text-slate-600">
            {t.text}
          </p>
          <div className="mt-8 space-y-4 text-sm text-slate-600">
            <p className="flex items-center gap-2">
              <Mail className="h-4 w-4 text-teal-600" />
              <a href="mailto:support@dxcon.com.vn" className="hover:text-teal-700">
                support@dxcon.com.vn
              </a>
            </p>
            <p className="flex items-center gap-2">
              <Phone className="h-4 w-4 text-teal-600" />
              <a href="tel:+84888895151" className="hover:text-teal-700">
                0888 895 151
              </a>
            </p>
            <p className="flex items-center gap-2">
              <MapPin className="h-4 w-4 text-teal-600" />
              {t.address}
            </p>
          </div>
        </div>
        <form className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="name">{t.name}</Label>
              <Input id="name" name="name" placeholder={t.namePh} />
            </div>
            <div>
              <Label htmlFor="organization">{t.org}</Label>
              <Input id="organization" name="organization" placeholder={t.orgPh} />
            </div>
          </div>
          <div className="mt-4">
            <Label htmlFor="email">{t.email}</Label>
            <Input id="email" name="email" type="email" placeholder="you@company.com" />
          </div>
          <div className="mt-4">
            <Label htmlFor="message">{t.message}</Label>
            <textarea
              id="message"
              name="message"
              rows={4}
              placeholder={t.messagePh}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
            />
          </div>
          <Button type="button" className="mt-6 w-full">
            {t.send}
          </Button>
        </form>
      </div>
    </section>
  );
}
