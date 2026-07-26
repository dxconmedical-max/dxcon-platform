"use client";

import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  QR_KIND_OPTIONS,
  fetchReceptionQrBundle,
  previewReceptionQrBundle,
  verifyReceptionQr,
  type ReceptionQrBundle,
  type ReceptionQrVerifyResult,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

const KIND_LABELS: Record<string, string> = {
  payment: "Payment QR",
  vnpay: "VNPay QR",
  static: "Static QR",
  dynamic: "Dynamic QR",
  sample: "Sample QR",
  tracking: "Tracking QR",
};

function openHtmlPrint(html: string) {
  const popup = window.open("", "_blank", "noopener,noreferrer,width=560,height=780");
  if (!popup) return;
  popup.document.write(html);
  popup.document.close();
}

export function QrWorkbench({ initialOrderRef = "" }: { initialOrderRef?: string }) {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = useMemo(
    () => ({ token: accessToken || "", organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [orderRef, setOrderRef] = useState(initialOrderRef);
  const [selected, setSelected] = useState<string[]>([...QR_KIND_OPTIONS]);
  const [amount, setAmount] = useState("");
  const [bundle, setBundle] = useState<ReceptionQrBundle | null>(null);
  const [verifyInput, setVerifyInput] = useState("");
  const [verifyResult, setVerifyResult] = useState<ReceptionQrVerifyResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const toggleKind = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const load = useCallback(async () => {
    if (!ctx.token || !orderRef.trim()) return;
    setBusy(true);
    setError(null);
    setVerifyResult(null);
    try {
      const amt = amount.trim() ? Number(amount) : undefined;
      const data = await fetchReceptionQrBundle(ctx, orderRef.trim(), {
        kinds: selected.length ? selected : undefined,
        amount: Number.isFinite(amt) ? amt : undefined,
        preview: true,
      });
      setBundle(data);
    } catch (err) {
      setError(normalizeApiError(err));
      setBundle(null);
    } finally {
      setBusy(false);
    }
  }, [ctx, orderRef, selected, amount]);

  async function onPreviewPrint() {
    if (!ctx.token || !orderRef.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const amt = amount.trim() ? Number(amount) : undefined;
      const data = await previewReceptionQrBundle(ctx, orderRef.trim(), {
        kinds: selected.length ? selected : undefined,
        amount: Number.isFinite(amt) ? amt : undefined,
      });
      setBundle(data);
      if (data.html) openHtmlPrint(data.html);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (!ctx.token || !verifyInput.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const result = await verifyReceptionQr(
        ctx,
        verifyInput.trim(),
        orderRef.trim() || undefined,
      );
      setVerifyResult(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-4 py-4">
      <label className="block space-y-1 text-sm">
        <span className="font-medium">Order ref</span>
        <div className="flex flex-wrap gap-2">
          <Input
            value={orderRef}
            onChange={(e) => setOrderRef(e.target.value)}
            placeholder="ORD-…"
          />
          <Input
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="Amount (optional)"
            className="max-w-[10rem]"
          />
          <Button type="button" disabled={busy || !orderRef.trim()} onClick={() => void load()}>
            Load QR pack
          </Button>
        </div>
      </label>

      <div className="flex flex-wrap gap-3 text-sm">
        {QR_KIND_OPTIONS.map((id) => (
          <label key={id} className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={selected.includes(id)}
              onChange={() => toggleKind(id)}
            />
            {KIND_LABELS[id] ?? id}
          </label>
        ))}
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={busy || !bundle} onClick={() => void onPreviewPrint()}>
          Print preview
        </Button>
      </div>

      {bundle ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {bundle.qrs.map((qr, idx) => (
            <div
              key={`${qr.kind}-${idx}`}
              className="space-y-2 rounded border border-neutral-200 p-3 text-sm"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-semibold">{qr.title || qr.kind}</span>
                <span className="text-xs uppercase text-neutral-500">
                  {qr.static ? "static" : "dynamic"}
                </span>
              </div>
              {qr.unavailable || !qr.payload ? (
                <p className="text-neutral-500">
                  Unavailable{qr.meta?.reason ? `: ${String(qr.meta.reason)}` : ""}
                </p>
              ) : (
                <>
                  {qr.image_data_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={qr.image_data_url}
                      alt={qr.title}
                      className="h-40 w-40 bg-white"
                    />
                  ) : null}
                  <button
                    type="button"
                    className="block w-full break-all text-left font-mono text-xs text-neutral-700 underline-offset-2 hover:underline"
                    onClick={() => setVerifyInput(qr.payload || "")}
                  >
                    {qr.payload}
                  </button>
                </>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-neutral-600">
          Load an order to generate payment, VNPay, static, dynamic, sample, and tracking QR codes.
        </p>
      )}

      <div className="space-y-2 rounded border border-dashed p-3">
        <p className="text-sm font-medium">Verification</p>
        <textarea
          className="min-h-[72px] w-full rounded border px-2 py-1 font-mono text-xs"
          value={verifyInput}
          onChange={(e) => setVerifyInput(e.target.value)}
          placeholder="Paste QR payload…"
        />
        <Button type="button" disabled={busy || !verifyInput.trim()} onClick={() => void onVerify()}>
          Verify payload
        </Button>
        {verifyResult ? (
          <p className={`text-sm ${verifyResult.valid ? "text-emerald-700" : "text-red-600"}`}>
            {verifyResult.valid ? "Valid" : "Invalid"} · {verifyResult.kind ?? "unknown"} ·{" "}
            {verifyResult.reason}
          </p>
        ) : null}
      </div>
    </div>
  );
}
