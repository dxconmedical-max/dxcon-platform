import Link from "next/link";
import { MapPin, Package, Smartphone } from "lucide-react";

import { LANDING, type Lang } from "@/lib/landing/i18n";

const ICONS = [Smartphone, MapPin, Package];

export function HomeCollectionSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].home;
  return (
    <section className="px-4 py-20 lg:px-8">
      <div className="mx-auto grid max-w-7xl items-center gap-10 lg:grid-cols-2">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            {t.eyebrow}
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">{t.title}</h2>
          <p className="mt-4 text-slate-600">{t.text}</p>
          <Link
            href="/book"
            className="mt-6 inline-flex items-center rounded-lg bg-teal-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-teal-700"
          >
            {t.cta}
          </Link>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {t.items.map((label, i) => {
            const Icon = ICONS[i];
            return (
              <div
                key={label}
                className="rounded-2xl border border-slate-200 bg-white p-5 text-center shadow-sm"
              >
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                  <Icon className="h-5 w-5" />
                </div>
                <p className="mt-3 text-sm font-medium text-slate-800">{label}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
