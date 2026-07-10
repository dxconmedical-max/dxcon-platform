import { Handshake, Hospital, Microscope } from "lucide-react";

export function PartnerSection() {
  return (
    <section id="partners" className="bg-slate-900 px-4 py-20 text-white lg:px-8">
      <div className="mx-auto max-w-7xl">
        <p className="text-sm font-semibold uppercase tracking-wide text-teal-300">
          Partner ecosystem
        </p>
        <h2 className="mt-2 text-3xl font-semibold lg:text-4xl">
          Built for labs, hospitals, and diagnostic networks
        </h2>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {[
            {
              icon: Microscope,
              title: "Reference laboratories",
              text: "High-volume processing, instrument interfaces, and partner portals.",
            },
            {
              icon: Hospital,
              title: "Hospital groups",
              text: "Multi-tenant governance with centralized reporting and SLAs.",
            },
            {
              icon: Handshake,
              title: "Clinic networks",
              text: "White-label patient experiences with shared catalog and pricing.",
            },
          ].map((partner) => {
            const Icon = partner.icon;
            return (
              <div
                key={partner.title}
                className="rounded-2xl border border-white/10 bg-white/5 p-6"
              >
                <Icon className="h-6 w-6 text-teal-300" />
                <h3 className="mt-4 text-lg font-semibold">{partner.title}</h3>
                <p className="mt-2 text-sm text-slate-300">{partner.text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
