import { IntegrationHub } from "@/components/integration/IntegrationHub";

export const metadata = { title: "Connectors" };

export default function ConnectorsPage() {
  return <IntegrationHub title="Connectors" subtitle="Manage organization-scoped integration connectors." />;
}
