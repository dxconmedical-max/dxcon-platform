import { Building2, FlaskConical, Stethoscope, Truck, Users } from "lucide-react";

import { LANDING, type Lang } from "@/lib/landing/i18n";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

const ICONS = [FlaskConical, Building2, Stethoscope, Users, Truck];

export function ServicesSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].services;
  const SERVICES = t.items.map(([title, description], i) => ({
    icon: ICONS[i],
    title,
    description,
  }));
  return (
    <section id="services" className="bg-white px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          {t.eyebrow}
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900 lg:text-4xl">
          {t.title}
        </h2>
        <p className="mt-4 max-w-2xl text-slate-600">
          {t.text}
        </p>
        <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {SERVICES.map((service) => {
            const Icon = service.icon;
            return (
              <Card key={service.title}>
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{service.title}</CardTitle>
                <CardDescription>{service.description}</CardDescription>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
