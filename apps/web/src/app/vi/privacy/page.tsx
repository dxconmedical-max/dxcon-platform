import type { Metadata } from "next";
import Link from "next/link";

import { Fill, LegalPage } from "@/components/legal/LegalPage";
import { SITE } from "@/lib/site";

export const metadata: Metadata = {
  title: "Chính sách bảo mật",
  description: "Cách DxCon thu thập, sử dụng và bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.",
  alternates: { canonical: "/vi/privacy" },
};

export default function PrivacyPage() {
  return (
    <LegalPage title="Chính sách bảo vệ dữ liệu cá nhân" updated={SITE.updated}>
      <p>
        Chính sách này mô tả cách <Fill value={SITE.legalName} /> (“DxCon”, “chúng tôi”), mã số thuế{" "}
        <Fill value={SITE.taxId} />, địa chỉ <Fill value={SITE.address} />, xử lý dữ liệu cá nhân của người
        dùng website và nền tảng dxcon.com.vn, phù hợp với Nghị định 13/2023/NĐ-CP về bảo vệ dữ liệu cá nhân
        và các quy định pháp luật liên quan.
      </p>

      <h2>1. Dữ liệu chúng tôi thu thập</h2>
      <ul>
        <li>Dữ liệu cá nhân cơ bản: họ tên, số điện thoại, email, địa chỉ lấy mẫu, ngày sinh, giới tính.</li>
        <li>
          Dữ liệu cá nhân nhạy cảm về sức khỏe: chỉ định xét nghiệm, mẫu bệnh phẩm, kết quả xét nghiệm, ghi chú
          lâm sàng do phòng khám hoặc phòng xét nghiệm cung cấp.
        </li>
        <li>Dữ liệu tài khoản và kỹ thuật: tên đăng nhập, vai trò, nhật ký truy cập, địa chỉ IP, loại thiết bị.</li>
        <li>Dữ liệu thanh toán: số tiền, trạng thái thanh toán. Chúng tôi không lưu số thẻ ngân hàng.</li>
      </ul>

      <h2>2. Mục đích xử lý</h2>
      <ul>
        <li>Tiếp nhận yêu cầu đặt lịch, lấy mẫu, chuyển mẫu đến phòng xét nghiệm thực hiện và trả kết quả.</li>
        <li>Liên hệ xác nhận lịch hẹn, thông báo trạng thái đơn và kết quả.</li>
        <li>Thanh toán, đối soát công nợ và xuất hóa đơn (do đơn vị thực hiện xét nghiệm phát hành khi cần).</li>
        <li>Bảo đảm an toàn hệ thống, phòng chống gian lận, tuân thủ nghĩa vụ pháp lý.</li>
        <li>Cải thiện chất lượng dịch vụ ở dạng thống kê đã loại bỏ thông tin định danh.</li>
      </ul>

      <h2>3. Cơ sở xử lý và sự đồng ý</h2>
      <p>
        Chúng tôi xử lý dữ liệu dựa trên sự đồng ý của chủ thể dữ liệu (ví dụ tích chọn đồng ý khi đặt lịch), để
        thực hiện hợp đồng/dịch vụ bạn yêu cầu, hoặc theo quy định pháp luật. Với dữ liệu nhạy cảm về sức khỏe,
        chúng tôi chỉ xử lý khi có sự đồng ý rõ ràng. Bạn có thể rút lại sự đồng ý bất cứ lúc nào bằng cách liên
        hệ chúng tôi; việc rút đồng ý không ảnh hưởng đến xử lý đã thực hiện trước đó.
      </p>

      <h2>4. Chia sẻ dữ liệu</h2>
      <p>Chúng tôi chỉ chia sẻ dữ liệu khi cần thiết cho dịch vụ, gồm:</p>
      <ul>
        <li>Phòng xét nghiệm thực hiện chỉ định xét nghiệm cho bạn;</li>
        <li>Phòng khám/bệnh viện đã chỉ định hoặc gửi mẫu cho bạn;</li>
        <li>Nhà cung cấp hạ tầng, nhắn tin, thanh toán hoạt động theo hợp đồng bảo mật với chúng tôi;</li>
        <li>Cơ quan nhà nước có thẩm quyền khi có yêu cầu hợp pháp.</li>
      </ul>
      <p>Chúng tôi không bán dữ liệu cá nhân của bạn.</p>

      <h2>5. Thời gian lưu trữ</h2>
      <p>
        Dữ liệu được lưu trong thời gian cần thiết cho mục đích nêu trên và theo thời hạn lưu trữ hồ sơ y tế,
        kế toán theo quy định pháp luật; sau đó được xóa hoặc ẩn danh hóa.
      </p>

      <h2>6. Biện pháp bảo vệ</h2>
      <p>
        Chúng tôi áp dụng phân quyền theo vai trò, mã hóa kết nối (HTTPS), ghi nhật ký truy cập, sao lưu định kỳ
        và giới hạn quyền truy cập dữ liệu sức khỏe cho nhân sự có nhiệm vụ liên quan.
      </p>

      <h2>7. Quyền của chủ thể dữ liệu</h2>
      <p>Theo Nghị định 13/2023/NĐ-CP, bạn có quyền:</p>
      <ul>
        <li>Được biết về việc xử lý dữ liệu của mình;</li>
        <li>Đồng ý hoặc không đồng ý, rút lại sự đồng ý;</li>
        <li>Truy cập, xem, chỉnh sửa hoặc yêu cầu chỉnh sửa dữ liệu;</li>
        <li>Yêu cầu cung cấp, xóa, hạn chế xử lý dữ liệu; phản đối xử lý;</li>
        <li>Khiếu nại, tố cáo, khởi kiện và yêu cầu bồi thường theo quy định pháp luật.</li>
      </ul>
      <p>
        Để thực hiện quyền, gửi yêu cầu đến <Fill value={SITE.privacyEmail} /> hoặc theo trang{" "}
        <Link href="/vi/contact">Liên hệ</Link>. Chúng tôi phản hồi trong thời hạn theo quy định pháp luật.
      </p>

      <h2>8. Cookie</h2>
      <p>
        Website dùng cookie cần thiết cho đăng nhập và bảo mật phiên làm việc. Bạn có thể tắt cookie trong trình
        duyệt, nhưng một số chức năng đăng nhập có thể không hoạt động.
      </p>

      <h2>9. Thay đổi chính sách</h2>
      <p>Chúng tôi có thể cập nhật chính sách này; phiên bản mới được đăng tại trang này kèm ngày cập nhật.</p>

      <h2>10. Liên hệ</h2>
      <p>
        <Fill value={SITE.legalName} /> — {" "}
        <Fill value={SITE.address} /> — Email: <Fill value={SITE.privacyEmail} /> — Điện thoại:{" "}
        <Fill value={SITE.phone} />.
      </p>
    </LegalPage>
  );
}
