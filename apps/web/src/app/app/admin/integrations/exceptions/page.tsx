import { IntegrationHub } from "@/components/integration/IntegrationHub";
export const metadata = { title: "Exceptions" };
export default function Page() {
  return <IntegrationHub title="Exception Queue" subtitle="Review failed imports and retry or ignore with reason." />;
}
