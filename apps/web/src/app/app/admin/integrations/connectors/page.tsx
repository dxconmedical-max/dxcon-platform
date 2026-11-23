import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Connectors" };

export default function Page() {
  return <IntegrationDataView title="Connectors" description="Các kết nối LIS, HIS, EMR, thanh toán đang đăng ký với DxCon." endpoint={"/api/v1/integration-hub/connectors"} />;
}
