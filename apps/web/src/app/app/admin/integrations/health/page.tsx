import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Health" };

export default function Page() {
  return <IntegrationDataView title="Health" description="Tình trạng các kết nối." endpoint={"/api/v1/integration-hub/health"} />;
}
