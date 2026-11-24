import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Ánh xạ mã" };

export default function Page() {
  return <IntegrationDataView title="Ánh xạ mã" description="Quy tắc ánh xạ mã xét nghiệm và trường dữ liệu." endpoint={null} />;
}
