export const FAQ_ITEMS: { q: string; a: string }[] = [
  {
    q: "DxCon là gì?",
    a: "DxCon là nền tảng kết nối bệnh nhân, phòng khám và phòng xét nghiệm: nhận yêu cầu, lấy mẫu tại nhà hoặc tại phòng khám, chuyển mẫu đến phòng xét nghiệm và trả kết quả.",
  },
  {
    q: "Làm sao để đặt lịch lấy mẫu tại nhà?",
    a: "Vào trang Đặt lịch, điền họ tên, số điện thoại, địa chỉ và khung giờ mong muốn. DxCon sẽ gọi xác nhận trước khi nhân viên đến.",
  },
  {
    q: "Tôi có cần nhịn ăn không?",
    a: "Tùy xét nghiệm. Nhân viên DxCon sẽ hướng dẫn cụ thể khi xác nhận lịch. Nếu chưa rõ, hãy hỏi trước khi lấy mẫu.",
  },
  {
    q: "Bao lâu có kết quả?",
    a: "Thời gian trả kết quả tùy loại xét nghiệm và phòng xét nghiệm thực hiện; chúng tôi sẽ báo thời gian dự kiến khi xác nhận.",
  },
  {
    q: "Thanh toán như thế nào?",
    a: "Bạn có thể thanh toán theo hướng dẫn khi xác nhận lịch. Với bệnh nhân của phòng khám đối tác, phòng khám có thể thu và DxCon thu hộ theo thỏa thuận.",
  },
  {
    q: "Dữ liệu sức khỏe của tôi có được bảo mật không?",
    a: "Có. Chúng tôi phân quyền theo vai trò, mã hóa kết nối và chỉ chia sẻ dữ liệu cho đơn vị trực tiếp thực hiện dịch vụ. Xem Chính sách bảo vệ dữ liệu cá nhân.",
  },
  {
    q: "Phòng khám muốn hợp tác thì làm thế nào?",
    a: "Vui lòng liên hệ qua trang Liên hệ hoặc gửi yêu cầu demo ở trang chủ. Đội ngũ DxCon sẽ trao đổi về bảng giá và cách gửi phiếu chỉ định.",
  },
];

export function Faq() {
  return (
    <div className="divide-y divide-slate-200 rounded-xl border border-slate-200">
      {FAQ_ITEMS.map((item) => (
        <details key={item.q} className="group p-4">
          <summary className="cursor-pointer list-none font-medium text-slate-900">{item.q}</summary>
          <p className="mt-2 text-slate-600">{item.a}</p>
        </details>
      ))}
    </div>
  );
}
