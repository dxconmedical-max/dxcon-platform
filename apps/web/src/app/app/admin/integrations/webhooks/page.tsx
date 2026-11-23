import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Webhooks" };

export default function Page() {
  return <IntegrationDataView title="Webhooks" description="Các webhook đăng ký nhận sự kiện từ DxCon." endpoint={"/api/v1/integration-hub/webhooks"} />;
}
