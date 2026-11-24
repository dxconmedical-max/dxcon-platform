import { IntegrationHub } from "@/components/integration/IntegrationHub";

export const metadata = { title: "Tích hợp" };

export default function IntegrationsPage() {
  return (
    <IntegrationHub
      title="Trung tâm tích hợp"
      subtitle="Kết nối trung lập với LIS, HIS, EMR, PACS, thanh toán và hệ thống đối tác. API: /api/v1/integration"
    />
  );
}
