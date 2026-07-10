import { IntegrationHub } from "@/components/integration/IntegrationHub";
export const metadata = { title: "Mappings" };
export default function Page() {
  return <IntegrationHub title="Mapping Rules" subtitle="Configure field, test code and unit mappings per connector." />;
}
