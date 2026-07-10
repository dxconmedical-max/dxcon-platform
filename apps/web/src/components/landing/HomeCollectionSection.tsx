import { MapPin, Package, Smartphone } from "lucide-react";

export function HomeCollectionSection() {
  return (
    <section className="px-4 py-20 lg:px-8">
      <div className="mx-auto grid max-w-7xl items-center gap-10 lg:grid-cols-2">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            Home collection
          </p>
          <h2 className="mt-2 text-3xl font-semibold text-slate-900">
            Door-to-lab logistics, orchestrated
          </h2>
          <p className="mt-4 text-slate-600">
            Dispatch collectors, track cold-chain compliance, and give patients
            real-time ETA updates from booking to lab receipt.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {[
            { icon: Smartphone, label: "Collector mobile app" },
            { icon: MapPin, label: "Live route tracking" },
            { icon: Package, label: "Chain-of-custody" },
          ].map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.label}
                className="rounded-2xl border border-slate-200 bg-white p-5 text-center shadow-sm"
              >
                <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-teal-700">
                  <Icon className="h-5 w-5" />
                </div>
                <p className="mt-3 text-sm font-medium text-slate-800">
                  {item.label}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
