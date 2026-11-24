import { Button } from "@/components/ui/Button";
import { LANDING, type Lang } from "@/lib/landing/i18n";

export function PricingSection({ lang }: { lang: Lang }) {
  const t = LANDING[lang].pricing;
  return (
    <section id="pricing" className="bg-white px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          {t.eyebrow}
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900">{t.title}</h2>
        <p className="mt-3 text-slate-600">{t.text}</p>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {t.plans.map((plan) => {
            const featured = "featured" in plan && plan.featured;
            return (
              <div
                key={plan.name}
                className={`rounded-2xl border p-6 ${
                  featured
                    ? "border-teal-500 bg-teal-50/40 shadow-lg shadow-teal-100"
                    : "border-slate-200 bg-white"
                }`}
              >
                <h3 className="text-lg font-semibold text-slate-900">{plan.name}</h3>
                <p className="mt-2 text-3xl font-semibold text-slate-900">{plan.price}</p>
                <ul className="mt-6 space-y-2 text-sm text-slate-600">
                  {plan.features.map((feature) => (
                    <li key={feature}>• {feature}</li>
                  ))}
                </ul>
                <a href="#contact">
                  <Button className="mt-6 w-full" variant={featured ? "primary" : "outline"}>
                    {t.cta}
                  </Button>
                </a>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
