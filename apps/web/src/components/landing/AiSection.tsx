import { BrainCircuit, LineChart, Shield } from "lucide-react";

import { LANDING, type Lang } from "@/lib/landing/i18n";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

const ICONS = [BrainCircuit, LineChart, Shield];

export function AiSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].ai;
  return (
    <section id="ai" className="bg-slate-50 px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          {t.eyebrow}
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900 lg:text-4xl">
          {t.title}
        </h2>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {t.items.map(([title, description], i) => {
            const Icon = ICONS[i];
            return (
              <Card key={title}>
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{description}</CardDescription>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
