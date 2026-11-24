import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Ngoại lệ" };

export default function Page() {
  return <IntegrationDataView title="Ngoại lệ" description="Tin nhắn lỗi hoặc bị kẹt (dead-letter), cần xử lý." endpoint={"/api/v1/integration-hub/dead-letters"} />;
}
