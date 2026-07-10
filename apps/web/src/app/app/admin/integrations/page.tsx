import { IntegrationHub } from "@/components/integration/IntegrationHub";

export const metadata = { title: "Integrations" };

export default function IntegrationsPage() {
  return (
    <IntegrationHub
      title="Integration Center"
      subtitle="Vendor-neutral connectors for LIS, HIS, EMR, PACS, payments and partner systems. API: /api/v1/integration"
    />
  );
}
