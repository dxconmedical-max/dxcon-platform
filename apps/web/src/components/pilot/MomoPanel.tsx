"use client";

import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { normalizeApiError } from "@/lib/errors";
import { apiRequest } from "@/services/api";

type Ctx = { token?: string | null; organizationId?: string | null };

type MomoCreate = { pay_url?: string | null; qr_png?: string | null; amount: number };

const unwrap = <T,>(res: T & { data?: T }): T => (res.data ?? res) as T;

export function MomoPanel({ orderRef, ctx, onPaid }: { orderRef: string; ctx: Ctx; onPaid: () => void }) {
  const [info, setInfo] = useState<MomoCreate | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  function stop() {
    if (timer.current !== null) window.clearInterval(timer.current);
    timer.current = null;
  }

  useEffect(() => stop, []);

  async function start() {
    setBusy(true);
    setError(null);
    try {
      const res = await apiRequest<MomoCreate & { data?: MomoCreate }>("/api/v1/payments/momo/create", {
        method: "POST",
        body: { order_ref: orderRef },
        token: ctx.token,
        organizationId: ctx.organizationId,
      });
      setInfo(unwrap(res));
      stop();
      timer.current = window.setInterval(async () => {
        try {
          const c = await apiRequest<{ paid: boolean; data?: { paid: boolean } }>(
            `/api/v1/payments/momo/check/${encodeURIComponent(orderRef)}`,
            { token: ctx.token, organizationId: ctx.organizationId },
          );
          if (unwrap(c).paid) {
            stop();
            setInfo(null);
            onPaid();
          }
        } catch {
          /* keep polling */
        }
      }, 4000);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3 rounded-lg border border-pink-200 bg-pink-50 p-4">
      <p className="text-sm font-medium">Thu qua MoMo</p>
      {!info ? (
        <Button variant="outline" disabled={busy} onClick={() => void start()}>
          {busy ? "Đang tạo mã…" : "Thu qua MoMo (QR)"}
        </Button>
      ) : (
        <div className="space-y-2 text-sm">
          {info.qr_png ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={info.qr_png} alt="QR MoMo" className="h-48 w-48 bg-white p-1" />
          ) : null}
          <p>
            Khách quét mã bằng app MoMo để trả <b>{info.amount.toLocaleString("vi-VN")} ₫</b>. Màn hình tự cập nhật khi
            MoMo xác nhận.
          </p>
          <div className="flex gap-2">
            {info.pay_url ? (
              <a className="text-sky-700 underline" href={info.pay_url} target="_blank" rel="noreferrer">
                Mở trang thanh toán
              </a>
            ) : null}
            <Button size="sm" variant="ghost" onClick={() => { stop(); setInfo(null); }}>
              Hủy mã
            </Button>
          </div>
        </div>
      )}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
