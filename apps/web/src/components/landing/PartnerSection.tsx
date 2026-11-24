import { Handshake, Hospital, Microscope } from "lucide-react";

import { LANDING, type Lang } from "@/lib/landing/i18n";

const ICONS = [Microscope, Hospital, Handshake];

export function PartnerSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].partners;
  return (
    <section id="partners" className="bg-slate-900 px-4 py-20 text-white lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-300">
          {t.eyebrow}
        </p>
        <h2 className="mt-2 text-3xl font-semibold lg:text-4xl">{t.title}</h2>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {t.items.map(([title, text], i) => {
            const Icon = ICONS[i];
            return (
              <div
                key={title}
                className="rounded-2xl border border-white/10 bg-white/5 p-6"
              >
                <Icon className="h-6 w-6 text-teal-300" />
                <h3 className="mt-4 text-lg font-semibold">{title}</h3>
                <p className="mt-2 text-sm text-slate-300">{text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
