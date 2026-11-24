"use client";

import { useEffect, useState } from "react";

type InstallEvent = Event & {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
};

function isStandalone(): boolean {
  if (typeof window === "undefined") return false;
  const nav = window.navigator as Navigator & { standalone?: boolean };
  return window.matchMedia("(display-mode: standalone)").matches || nav.standalone === true;
}

export function InstallAppCard() {
  const [installed, setInstalled] = useState(true);
  const [platform, setPlatform] = useState<"ios" | "android" | "other">("other");
  const [deferred, setDeferred] = useState<InstallEvent | null>(null);
  const [notSafari, setNotSafari] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setInstalled(isStandalone());
    const ua = navigator.userAgent;
    if (/iPhone|iPad|iPod/i.test(ua)) {
      setPlatform("ios");
      setNotSafari(/CriOS|FxiOS|EdgiOS|OPiOS|Zalo|FBAN|FBAV|Instagram/i.test(ua));
    }
    else if (/Android/i.test(ua)) setPlatform("android");
    const onPrompt = (e: Event) => {
      e.preventDefault();
      setDeferred(e as InstallEvent);
    };
    const onInstalled = () => setInstalled(true);
    window.addEventListener("beforeinstallprompt", onPrompt);
    window.addEventListener("appinstalled", onInstalled);
    return () => {
      window.removeEventListener("beforeinstallprompt", onPrompt);
      window.removeEventListener("appinstalled", onInstalled);
    };
  }, []);

  if (installed) return null;

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.origin + "/app/collector");
      setCopied(true);
    } catch {
      window.prompt("Sao chép liên kết này rồi dán vào Safari:", window.location.origin + "/app/collector");
    }
  }

  async function install() {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
  }

  return (
    <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-950">
      <h2 className="text-base font-semibold">Cài DxCon lên điện thoại</h2>
      <p className="mt-1">Cài một lần, mở từ màn hình chính như một ứng dụng.</p>
      {deferred ? (
        <button
          type="button"
          onClick={() => void install()}
          className="mt-3 rounded-lg bg-emerald-700 px-4 py-2 font-medium text-white"
        >
          Cài ứng dụng
        </button>
      ) : null}
      {platform === "ios" && notSafari ? (
        <div className="mt-3 rounded-lg bg-amber-50 p-3 text-amber-900">
          <p>
            iPhone chỉ cho cài ứng dụng bằng <strong>Safari</strong>, nên không có nút cài ở trình duyệt này.
            Bấm nút dưới đây, mở Safari, dán liên kết vào ô địa chỉ.
          </p>
          <button
            type="button"
            onClick={() => void copyLink()}
            className="mt-2 rounded-lg bg-amber-600 px-4 py-2 font-medium text-white"
          >
            {copied ? "Đã sao chép — mở Safari và dán" : "Sao chép liên kết cho Safari"}
          </button>
        </div>
      ) : null}
      {platform === "ios" ? (
        <ol className="mt-3 list-decimal space-y-1 pl-5">
          <li>Mở trang này bằng <strong>Safari</strong> (không dùng Zalo, Facebook hay Chrome).</li>
          <li>Bấm nút <strong>Chia sẻ</strong> (ô vuông có mũi tên lên) hoặc nút <strong>•••</strong> ở thanh dưới, rồi chọn Chia sẻ.</li>
          <li>Vuốt lên, chọn <strong>Thêm vào Màn hình chính</strong>, rồi bấm <strong>Thêm</strong>.</li>
        </ol>
      ) : null}
      {platform === "android" && !deferred ? (
        <ol className="mt-3 list-decimal space-y-1 pl-5">
          <li>Mở trang này bằng <strong>Chrome</strong>.</li>
          <li>Bấm <strong>ba chấm</strong> góc trên bên phải.</li>
          <li>Chọn <strong>Cài đặt ứng dụng</strong> hoặc <strong>Thêm vào màn hình chính</strong>.</li>
        </ol>
      ) : null}
      {platform === "other" && !deferred ? (
        <p className="mt-3">
          Hãy mở trang này trên điện thoại. iPhone dùng Safari, Android dùng Chrome.
        </p>
      ) : null}
    </section>
  );
}
