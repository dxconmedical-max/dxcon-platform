import { AppShell } from "@/components/layout/AppShell";
import { Card, CardDescription, CardTitle } from "@/components/ui/Card";
import Link from "next/link";

export function IntegrationHub({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <AppShell title={title} workspacePath="/app/admin">
      <div className="space-y-6">
        <section className="rounded-2xl border border-slate-200 bg-white p-6">
          <h2 className="text-2xl font-semibold text-slate-900">{title}</h2>
          <p className="mt-2 text-slate-600">{subtitle}</p>
        </section>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[
            ["/app/admin/integrations/connectors", "Connectors", "LIS, HIS, EMR, PACS and custom API connectors"],
            ["/app/admin/integrations/messages", "Messages", "Inbound and outbound integration messages"],
            ["/app/admin/integrations/exceptions", "Exceptions", "Failed and dead-letter queue"],
            ["/app/admin/integrations/mappings", "Mappings", "Field and test code mapping rules"],
            ["/app/admin/integrations/webhooks", "Webhooks", "Event subscriptions and deliveries"],
            ["/app/admin/integrations/health", "Health", "Connector health and throughput metrics"],
          ].map(([href, label, desc]) => (
            <Card key={href}>
              <CardTitle>{label}</CardTitle>
              <CardDescription>{desc}</CardDescription>
              <Link href={href} className="mt-4 inline-block text-sm font-medium text-teal-700">
                Open
              </Link>
            </Card>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
