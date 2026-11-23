import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Mappings" };

export default function Page() {
  return <IntegrationDataView title="Mappings" description="Quy tắc ánh xạ mã xét nghiệm và trường dữ liệu." endpoint={null} />;
}
