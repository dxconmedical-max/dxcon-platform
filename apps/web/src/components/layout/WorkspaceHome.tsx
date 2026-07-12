import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";

export type WorkspaceAction = {
  label: string;
  href: string;
  description?: string;
  comingSoon?: boolean;
};

export type StatusCard = {
  label: string;
  value: string;
  hint?: string;
};

export function WorkspaceHome({
  title,
  subtitle,
  statusCards,
  actions,
  loading = false,
  error = null,
  dataLoaded = false,
}: {
  title: string;
  subtitle: string;
  statusCards: StatusCard[];
  actions: WorkspaceAction[];
  loading?: boolean;
  error?: string | null;
  dataLoaded?: boolean;
}) {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-teal-50/40 p-6 lg:p-8">
        <Badge tone="info">Production workspace</Badge>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-slate-900 lg:text-3xl">
          {title}
        </h2>
        <p className="mt-2 max-w-2xl text-slate-600">{subtitle}</p>
        {loading ? (
          <p className="mt-3 text-sm text-slate-500">Loading workspace metrics…</p>
        ) : null}
        {error ? (
          <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-sm text-amber-800" role="status">
            Metrics unavailable: {error}. Showing placeholders until API access is confirmed.
          </p>
        ) : null}
        {dataLoaded && !error ? (
          <p className="mt-3 text-xs text-slate-500">Metrics loaded from production API.</p>
        ) : null}
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {statusCards.map((card) => (
          <Card key={card.label}>
            <p className="text-sm text-slate-500">{card.label}</p>
            <p className="mt-2 text-2xl font-semibold text-slate-900">{card.value}</p>
            {card.hint ? (
              <p className="mt-1 text-xs text-slate-500">{card.hint}</p>
            ) : null}
          </Card>
        ))}
      </section>

      <section>
        <h3 className="mb-4 text-lg font-semibold text-slate-900">Key actions</h3>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {actions.map((action) => (
            <Card key={action.label} className="flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <CardTitle>{action.label}</CardTitle>
                  {action.comingSoon ? <Badge>Coming soon</Badge> : null}
                </div>
                {action.description ? (
                  <CardDescription>{action.description}</CardDescription>
                ) : null}
              </div>
              {action.comingSoon ? (
                <span className="mt-4 inline-flex items-center gap-1 text-sm text-slate-400">
                  Planned module
                </span>
              ) : (
                <Link
                  href={action.href}
                  className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-teal-700 hover:text-teal-800"
                >
                  Open module
                  <ArrowRight className="h-4 w-4" />
                </Link>
              )}
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
