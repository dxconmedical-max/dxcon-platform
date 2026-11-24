import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Kết nối" };

export default function Page() {
  return <IntegrationDataView title="Kết nối" description="Các kết nối LIS, HIS, EMR, thanh toán đang đăng ký với DxCon." endpoint={"/api/v1/integration-hub/connectors"} />;
}
