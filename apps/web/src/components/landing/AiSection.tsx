import { BrainCircuit, LineChart, Shield } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export function AiSection() {
  return (
    <section id="ai" className="bg-slate-50 px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          AI intelligence
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900 lg:text-4xl">
          Clinical insights with human oversight
        </h2>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {[
            {
              icon: BrainCircuit,
              title: "Interpretation assist",
              description:
                "Highlight critical values and suggest follow-up panels based on clinical context.",
            },
            {
              icon: LineChart,
              title: "Operational analytics",
              description:
                "Forecast demand, monitor TAT, and identify bottlenecks across sites.",
            },
            {
              icon: Shield,
              title: "Governed AI",
              description:
                "Audit trails, role-based access, and clinician review before patient release.",
            },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <Card key={item.title}>
                <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-slate-900 text-white">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{item.title}</CardTitle>
                <CardDescription>{item.description}</CardDescription>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
