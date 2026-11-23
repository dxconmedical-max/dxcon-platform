import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Messages" };

export default function Page() {
  return <IntegrationDataView title="Messages" description="Tin nhắn đến và đi giữa DxCon và hệ thống ngoài." endpoint={"/api/v1/integrations/messages"} />;
}
