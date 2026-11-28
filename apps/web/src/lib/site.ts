// Thông tin pháp nhân hiển thị trên website.
// Các giá trị dạng [CẦN ĐIỀN: ...] là chỗ trống — Brian cập nhật tại đây, mọi trang sẽ tự đổi theo.
export const SITE = {
  url: "https://dxcon.com.vn",
  brand: "DxCon",
  legalName: "[CẦN ĐIỀN: Tên pháp nhân đầy đủ]",
  taxId: "[CẦN ĐIỀN: Mã số thuế]",
  address: "[CẦN ĐIỀN: Địa chỉ trụ sở]",
  phone: "[CẦN ĐIỀN: Số điện thoại]",
  email: "[CẦN ĐIỀN: Email liên hệ]",
  privacyEmail: "[CẦN ĐIỀN: Email tiếp nhận yêu cầu về dữ liệu cá nhân]",
  hours: "[CẦN ĐIỀN: Giờ làm việc, ví dụ 08:00–17:30 Thứ Hai–Thứ Bảy]",
  updated: "28/11/2026",
};

export const isPlaceholder = (v: string) => v.startsWith("[CẦN ĐIỀN");
