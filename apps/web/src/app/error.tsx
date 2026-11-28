"use client";

import Link from "next/link";

export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4 text-center">
      <h1 className="text-2xl font-semibold text-slate-900">Đã có lỗi xảy ra</h1>
      <p className="mt-2 max-w-md text-slate-600">
        Hệ thống gặp sự cố tạm thời. Bạn thử tải lại; nếu vẫn lỗi, vui lòng liên hệ hỗ trợ.
      </p>
      {error.digest ? <p className="mt-2 text-xs text-slate-400">Mã lỗi: {error.digest}</p> : null}
      <div className="mt-6 flex gap-3">
        <button
          type="button"
          onClick={() => reset()}
          className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700"
        >
          Thử lại
        </button>
        <Link href="/" className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-white">
          Về trang chủ
        </Link>
      </div>
    </main>
  );
}
