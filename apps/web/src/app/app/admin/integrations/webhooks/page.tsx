import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Webhook" };

export default function Page() {
  return <IntegrationDataView title="Webhook" description="Các webhook đăng ký nhận sự kiện từ DxCon." endpoint={"/api/v1/integration-hub/webhooks"} />;
}
