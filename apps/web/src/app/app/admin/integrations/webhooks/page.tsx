import { IntegrationHub } from "@/components/integration/IntegrationHub";
export const metadata = { title: "Webhooks" };
export default function Page() {
  return <IntegrationHub title="Webhooks" subtitle="HTTPS subscriptions with HMAC signing and delivery history." />;
}
