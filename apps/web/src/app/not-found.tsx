import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
      <p className="text-6xl font-semibold text-teal-700">404</p>
      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Không tìm thấy trang</h1>
      <p className="mt-2 max-w-md text-slate-600">
        Đường dẫn bạn truy cập không tồn tại hoặc đã được chuyển. Vui lòng kiểm tra lại địa chỉ.
      </p>
      <div className="mt-6 flex gap-3">
        <Link href="/" className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700">
          Về trang chủ
        </Link>
        <Link href="/vi/contact" className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white">
          Liên hệ hỗ trợ
        </Link>
      </div>
    </main>
  );
}
