"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import { submitPublicBooking, type BookingSlot } from "@/lib/api/publicBooking";

const SLOT_LABELS: Record<BookingSlot, string> = {
  ANYTIME: "Giờ nào cũng được",
  MORNING: "Buổi sáng",
  AFTERNOON: "Buổi chiều",
};

export default function PublicBookingPage() {
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [address, setAddress] = useState("");
  const [district, setDistrict] = useState("");
  const [preferredDate, setPreferredDate] = useState("");
  const [slot, setSlot] = useState<BookingSlot>("ANYTIME");
  const [note, setNote] = useState("");
  const [consent, setConsent] = useState(false);
  const [website, setWebsite] = useState(""); // honeypot
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reference, setReference] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await submitPublicBooking({
        full_name: fullName.trim(),
        phone: phone.trim(),
        email: email.trim() || undefined,
        address: address.trim(),
        district: district.trim() || undefined,
        preferred_date: preferredDate || undefined,
        preferred_slot: slot,
        note: note.trim() || undefined,
        consent_contact: consent,
        website,
      });
      setReference(result.reference);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  if (reference) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
        <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-semibold">Đã nhận yêu cầu</h1>
          <p className="mt-3 text-sm text-slate-700">
            DxCon sẽ liên hệ lại với bạn để xác nhận lịch lấy mẫu. Mã yêu cầu của bạn:
          </p>
          <p className="mt-2 text-lg font-semibold text-teal-700">{reference}</p>
          <p className="mt-4 text-xs text-slate-500">
            Đây mới là yêu cầu đặt lịch, chưa phải xác nhận lịch hẹn.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 py-10">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Đặt lịch lấy mẫu xét nghiệm</h1>
        <p className="mt-2 text-sm text-slate-600">
          Để lại thông tin, DxCon sẽ gọi lại để xác nhận lịch. Vui lòng <strong>không</strong> nhập
          thông tin bệnh hay kết quả khám vào biểu mẫu này.
        </p>
        <form className="mt-6 space-y-4" onSubmit={handleSubmit}>
          <div>
            <Label htmlFor="full_name">Họ và tên *</Label>
            <Input id="full_name" required maxLength={120} value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="phone">Số điện thoại *</Label>
            <Input id="phone" type="tel" required inputMode="tel" placeholder="0901234567" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="email">Email (không bắt buộc)</Label>
            <Input id="email" type="email" maxLength={120} value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="address">Địa chỉ lấy mẫu *</Label>
            <Input id="address" required maxLength={300} value={address} onChange={(e) => setAddress(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="district">Quận / huyện</Label>
            <Input id="district" maxLength={100} value={district} onChange={(e) => setDistrict(e.target.value)} />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="preferred_date">Ngày mong muốn</Label>
              <Input id="preferred_date" type="date" value={preferredDate} onChange={(e) => setPreferredDate(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="slot">Khung giờ</Label>
              <select
                id="slot"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                value={slot}
                onChange={(e) => setSlot(e.target.value as BookingSlot)}
              >
                {(Object.keys(SLOT_LABELS) as BookingSlot[]).map((key) => (
                  <option key={key} value={key}>{SLOT_LABELS[key]}</option>
                ))}
              </select>
            </div>
          </div>
          <div>
            <Label htmlFor="note">Ghi chú (ví dụ: gọi trước khi đến)</Label>
            <Input id="note" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          <div aria-hidden="true" style={{ position: "absolute", left: "-10000px", height: 0, overflow: "hidden" }}>
            <label htmlFor="website">Website</label>
            <input id="website" tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
          </div>
          <label className="flex items-start gap-2 text-sm text-slate-700">
            <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
            <span>
              Tôi đồng ý để DxCon liên hệ lại với tôi qua điện thoại, tin nhắn hoặc email về yêu cầu
              đặt lịch này, và đã đọc{" "}
              <a href="/vi/privacy" target="_blank" rel="noreferrer" className="text-teal-700 underline">Chính sách bảo mật</a>{" "}
              và{" "}
              <a href="/vi/terms" target="_blank" rel="noreferrer" className="text-teal-700 underline">Điều khoản sử dụng</a>.
            </span>
          </label>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <Button type="submit" className="w-full" disabled={loading || !consent}>
            {loading ? "Đang gửi..." : "Gửi yêu cầu đặt lịch"}
          </Button>
        </form>
      </div>
    </div>
  );
}
