import { Building2, FlaskConical, Stethoscope, Truck, Users } from "lucide-react";

import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

const SERVICES = [
  {
    icon: FlaskConical,
    title: "Laboratory operations",
    description:
      "Worklists, result verification, QC workflows, and partner integrations in one hub.",
  },
  {
    icon: Building2,
    title: "Clinic management",
    description:
      "Reception, scheduling, billing, and patient communication for multi-site clinics.",
  },
  {
    icon: Stethoscope,
    title: "Doctor workspace",
    description:
      "Review results, collaborate with labs, and manage patient care pathways.",
  },
  {
    icon: Users,
    title: "Patient portal",
    description:
      "Secure access to results, appointments, and home collection requests.",
  },
  {
    icon: Truck,
    title: "Home collection",
    description:
      "Route optimization, collector mobile tools, and real-time sample tracking.",
  },
];

export function ServicesSection() {
  return (
    <section id="services" className="bg-white px-4 py-20 lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
          Product overview
        </p>
        <h2 className="mt-2 text-3xl font-semibold text-slate-900 lg:text-4xl">
          One platform for the full diagnostics journey
        </h2>
        <p className="mt-4 max-w-2xl text-slate-600">
          From order intake to verified results, DxCon connects every stakeholder
          with role-based workspaces and real-time visibility.
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
