import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Tình trạng" };

export default function Page() {
  return <IntegrationDataView title="Tình trạng" description="Tình trạng các kết nối." endpoint={"/api/v1/integration-hub/health"} />;
}
