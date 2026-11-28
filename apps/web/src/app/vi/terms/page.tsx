import type { Metadata } from "next";
import Link from "next/link";

import { Fill, LegalPage } from "@/components/legal/LegalPage";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Điều khoản sử dụng",
  description: "Điều khoản sử dụng website và nền tảng DxCon.",
  alternates: { canonical: "/vi/terms" },
};

export default function TermsPage() {
  return (
    <LegalPage title="Điều khoản sử dụng" updated={SITE.updated}>
      <p>
        Khi truy cập website hoặc sử dụng nền tảng DxCon do <Fill value={SITE.legalName} /> (mã số thuế{" "}
        <Fill value={SITE.taxId} />) vận hành, bạn đồng ý với các điều khoản dưới đây.
      </p>

      <h2>1. Vai trò của DxCon</h2>
      <p>
        DxCon là nền tảng kết nối phòng khám, bệnh nhân và phòng xét nghiệm: tiếp nhận yêu cầu, thu và vận
        chuyển mẫu, chuyển cho phòng xét nghiệm thực hiện và chuyển kết quả. Việc thực hiện xét nghiệm và kết
        quả chuyên môn do phòng xét nghiệm được cấp phép chịu trách nhiệm. DxCon không thay thế chẩn đoán hay
        tư vấn của bác sĩ.
      </p>

      <h2>2. Tài khoản</h2>
      <ul>
        <li>Bạn cung cấp thông tin chính xác và bảo mật thông tin đăng nhập của mình.</li>
        <li>Mọi hoạt động từ tài khoản của bạn được xem là do bạn thực hiện; hãy báo ngay khi nghi ngờ bị lộ.</li>
        <li>Chúng tôi có thể tạm khóa tài khoản có dấu hiệu vi phạm hoặc gây rủi ro an toàn hệ thống.</li>
      </ul>

      <h2>3. Đặt lịch và lấy mẫu</h2>
      <p>
        Yêu cầu đặt lịch chỉ được xem là xác nhận khi DxCon liên hệ xác nhận. Bạn cung cấp đúng thông tin cá nhân
        và chỉ định (nếu có), tuân thủ hướng dẫn chuẩn bị (ví dụ nhịn ăn). Mẫu không đạt yêu cầu có thể phải lấy
        lại.
      </p>

      <h2>4. Giá và thanh toán</h2>
      <p>
        Giá hiển thị là giá niêm yết hoặc giá theo thỏa thuận với phòng khám/đối tác. Chúng tôi có thể thu hộ
        phí xét nghiệm; hóa đơn (nếu cần) do đơn vị thực hiện xét nghiệm phát hành. Giá có thể thay đổi và được
        thông báo trước khi bạn xác nhận.
      </p>

      <h2>5. Kết quả xét nghiệm</h2>
      <p>
        Kết quả được cung cấp cho đúng người được ủy quyền. Hãy trao đổi với bác sĩ để được giải thích kết quả.
        Các gợi ý do công cụ tự động/AI (nếu có) chỉ mang tính tham khảo cho nhân sự chuyên môn.
      </p>

      <h2>6. Hành vi bị cấm</h2>
      <ul>
        <li>Giả mạo danh tính, cung cấp thông tin sai lệch;</li>
        <li>Truy cập trái phép, dò quét, phá hoại hoặc làm quá tải hệ thống;</li>
        <li>Sao chép, khai thác dữ liệu hàng loạt không được phép;</li>
        <li>Sử dụng nền tảng vào mục đích trái pháp luật.</li>
      </ul>

      <h2>7. Sở hữu trí tuệ</h2>
      <p>
        Nhãn hiệu, giao diện, phần mềm và nội dung của DxCon thuộc quyền của chúng tôi hoặc bên cấp phép. Bạn
        không được sao chép hoặc sử dụng khi chưa có sự đồng ý bằng văn bản.
      </p>

      <h2>8. Giới hạn trách nhiệm</h2>
      <p>
        Trong phạm vi pháp luật cho phép, DxCon không chịu trách nhiệm cho thiệt hại gián tiếp, hoặc do sự kiện
        bất khả kháng, lỗi hạ tầng bên thứ ba, hoặc do bạn cung cấp thông tin sai. Điều này không loại trừ trách
        nhiệm mà pháp luật không cho phép loại trừ.
      </p>

      <h2>9. Bảo vệ dữ liệu cá nhân</h2>
      <p>
        Việc xử lý dữ liệu cá nhân được quy định tại <Link href="/vi/privacy">Chính sách bảo vệ dữ liệu cá nhân</Link>.
      </p>

      <h2>10. Thay đổi điều khoản</h2>
      <p>Chúng tôi có thể cập nhật điều khoản; việc tiếp tục sử dụng sau khi đăng bản mới nghĩa là bạn chấp nhận.</p>

      <h2>11. Luật áp dụng và giải quyết tranh chấp</h2>
      <p>
        Điều khoản này chịu sự điều chỉnh của pháp luật Việt Nam. Tranh chấp được ưu tiên giải quyết bằng thương
        lượng; nếu không thành, đưa ra Tòa án có thẩm quyền tại Việt Nam.
      </p>

      <h2>12. Liên hệ</h2>
      <p>
        <Fill value={SITE.legalName} />, <Fill value={SITE.address} />, Email: <Fill value={SITE.email} />, Điện
        thoại: <Fill value={SITE.phone} />.
      </p>
    </LegalPage>
  );
}
