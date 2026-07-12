import type { MessageTree } from "./en";

/** Vietnamese strings — structure mirrors English; copy can be localized incrementally. */
export const vi: MessageTree = {
  nav: {
    services: "Dịch vụ",
    ai: "AI",
    partners: "Đối tác",
    pricing: "Bảng giá",
    contact: "Liên hệ",
    signIn: "Đăng nhập",
    bookDemo: "Đặt lịch demo",
  },
  hero: {
    badge: "Nền tảng chẩn đoán y tế",
    title: "Kết nối phòng xét nghiệm, phòng khám và bệnh nhân trên một nền tảng tin cậy",
    subtitle:
      "DxCon thống nhất đơn hàng, lấy mẫu tại nhà, vận hành lab và báo cáo lâm sàng với bảo mật doanh nghiệp và hỗ trợ AI.",
    contactSales: "Liên hệ kinh doanh",
    previewLabel: "Xem trước minh họa nền tảng",
    previewNote:
      "Tổng quan tính năng để đánh giá. Số liệu vận hành có trong workspace đã xác thực.",
    trust: {
      security: "Kiến trúc ưu tiên bảo mật",
      rbac: "Phân quyền theo vai trò",
      audit: "Quy trình sẵn sàng kiểm toán",
      ai: "Hỗ trợ AI có giám sát của chuyên gia",
    },
    card: {
      orders: {
        title: "Điều phối đơn hàng",
        text: "Quy trình từ tiếp nhận đến lab với mã vạch và thanh toán.",
      },
      ai: {
        title: "Hỗ trợ quyết định lâm sàng",
        text: "Gợi ý tư vấn với bắt buộc bác sĩ xem xét.",
      },
      partners: {
        title: "Mạng đối tác",
        text: "Quản trị đa tenant cho lab, phòng khám và bệnh viện.",
      },
      security: {
        title: "Cô lập tenant",
        text: "Truy cập theo tổ chức với nhật ký kiểm toán.",
      },
    },
  },
  footer: {
    tagline: "Chẩn đoán kết nối cho chăm sóc sức khỏe hiện đại.",
    privacy: "Quyền riêng tư",
    terms: "Điều khoản",
  },
  bookDemo: {
    title: "Đặt lịch demo",
    subtitle: "Cho chúng tôi biết về tổ chức của bạn để sắp xếp buổi giới thiệu.",
    submit: "Gửi yêu cầu demo",
  },
  contact: {
    title: "Liên hệ kinh doanh",
    subtitle: "Liên hệ đội DxCon về hợp tác, thí điểm và triển khai doanh nghiệp.",
  },
};
