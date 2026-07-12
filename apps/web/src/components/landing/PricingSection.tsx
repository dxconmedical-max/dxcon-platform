import Link from "next/link";

import { Button } from "@/components/ui/Button";

const PLANS = [
  {
    name: "Clinic",
    price: "Contact us",
    features: ["Up to 5 sites", "Patient portal", "Basic reporting"],
  },
  {
    name: "Laboratory",
    price: "Contact us",
    featured: true,
    features: ["LIS integrations", "Home collection", "AI insights"],
  },
  {
    name: "Enterprise",
    price: "Contact us",
    features: ["Multi-tenant", "Custom SLAs", "Dedicated support"],
  },
];

export function PricingSection() {
  return (
    <section id="pricing" className="bg-white px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Pricing
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900">
          Flexible plans for every stage
        </h2>
        <p className="mt-3 text-slate-600">
          Pricing placeholder — contact our team for a tailored quote.
        </p>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`rounded-2xl border p-6 ${
                plan.featured
                  ? "border-teal-500 bg-teal-50/40 shadow-lg shadow-teal-100"
                  : "border-slate-200 bg-white"
              }`}
            >
              <h3 className="text-lg font-semibold text-slate-900">{plan.name}</h3>
              <p className="mt-2 text-3xl font-semibold text-slate-900">
                {plan.price}
              </p>
              <ul className="mt-6 space-y-2 text-sm text-slate-600">
                {plan.features.map((feature) => (
                  <li key={feature}>• {feature}</li>
                ))}
              </ul>
              <Link href="/book-demo">
                <Button className="mt-6 w-full" variant={plan.featured ? "primary" : "outline"}>
                  Request quote
                </Button>
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
