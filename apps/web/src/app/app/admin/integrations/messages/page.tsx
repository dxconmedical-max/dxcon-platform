import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Tin nhắn" };

export default function Page() {
  return <IntegrationDataView title="Tin nhắn" description="Tin nhắn đến và đi giữa DxCon và hệ thống ngoài." endpoint={"/api/v1/integrations/messages"} />;
}
