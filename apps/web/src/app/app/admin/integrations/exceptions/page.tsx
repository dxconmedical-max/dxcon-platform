import { IntegrationDataView } from "@/components/integration/IntegrationDataView";

export const metadata = { title: "Exceptions" };

export default function Page() {
  return <IntegrationDataView title="Exceptions" description="Tin nhắn lỗi hoặc bị kẹt (dead-letter), cần xử lý." endpoint={"/api/v1/integration-hub/dead-letters"} />;
}
