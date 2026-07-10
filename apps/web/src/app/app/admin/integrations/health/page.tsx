import { IntegrationHub } from "@/components/integration/IntegrationHub";
export const metadata = { title: "Integration Health" };
export default function Page() {
  return <IntegrationHub title="Integration Health" subtitle="Active connectors, success rate, retries and dead-letter counts." />;
}
