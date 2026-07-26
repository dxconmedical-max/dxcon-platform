"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  cancelReceptionReceipt,
  fetchOrderReceipts,
  fetchReceptionReceipt,
  previewReceptionReceipt,
  printReceptionReceipt,
  receptionReceiptPdfUrl,
  reprintReceptionReceipt,
  type ReceptionReceiptRecord,
} from "@/lib/api/reception";

function openHtmlPrint(html: string) {
  const popup = window.open("", "_blank", "noopener,noreferrer,width=480,height=720");
  if (!popup) return;
  popup.document.write(html);
  popup.document.close();
}

export function ReceiptWorkbench({
  initialOrderRef = "",
  initialReceiptCode = "",
}: {
  initialOrderRef?: string;
  initialReceiptCode?: string;
}) {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = useMemo(
    () => ({ token: accessToken || "", organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [orderRef, setOrderRef] = useState(initialOrderRef);
  const [receiptCode, setReceiptCode] = useState(initialReceiptCode);
  const [receipts, setReceipts] = useState<ReceptionReceiptRecord[]>([]);
  const [active, setActive] = useState<ReceptionReceiptRecord | null>(null);
  const [html, setHtml] = useState("");
  const [thermalText, setThermalText] = useState("");
  const [format, setFormat] = useState<"standard" | "thermal">("standard");
  const [cancelReason, setCancelReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const loadReceipt = useCallback(
    async (code: string) => {
      if (!ctx.token || !code) return;
      setBusy(true);
      setError(null);
      try {
        const data = await fetchReceptionReceipt(ctx, code);
        setActive(data.receipt);
        setReceiptCode(data.receipt?.receipt_code || code);
        const preview =
          format === "thermal"
            ? await previewReceptionReceipt(ctx, code, "thermal")
            : null;
        setHtml(
          format === "thermal"
            ? preview?.html || data.preview.thermal_html || data.preview.html
            : data.preview.html,
        );
        setThermalText(data.preview.thermal_text || preview?.thermal_text || "");
      } catch (err) {
        setError(normalizeApiError(err));
      } finally {
        setBusy(false);
      }
    },
    [ctx, format],
  );

  const loadOrderReceipts = useCallback(async () => {
    if (!ctx.token || !orderRef.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const data = await fetchOrderReceipts(ctx, orderRef.trim());
      setReceipts(data.receipts);
      if (data.receipts[0]) {
        await loadReceipt(data.receipts[0].receipt_code);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }, [ctx, orderRef, loadReceipt]);

  useEffect(() => {
    const t = window.setTimeout(() => {
      if (initialReceiptCode) void loadReceipt(initialReceiptCode);
      else if (initialOrderRef) void loadOrderReceipts();
    }, 0);
    return () => window.clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onPrint(asReprint: boolean) {
    if (!active || !ctx.token) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = asReprint
        ? await reprintReceptionReceipt(ctx, active.receipt_code, format)
        : await printReceptionReceipt(ctx, active.receipt_code, format);
      setActive(result.receipt);
      const nextHtml =
        format === "thermal"
          ? result.preview.thermal_html || result.preview.html
          : result.preview.html;
      setHtml(nextHtml);
      setThermalText(result.preview.thermal_text || "");
      openHtmlPrint(nextHtml);
      setMessage(asReprint ? "Reprint recorded." : "Print recorded.");
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onCancel() {
    if (!active || !ctx.token) return;
    setBusy(true);
    setError(null);
    try {
      const result = await cancelReceptionReceipt(ctx, active.receipt_code, cancelReason || undefined);
      setActive(result.receipt);
      setMessage("Receipt cancelled.");
      await loadReceipt(active.receipt_code);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const cancelled = active?.status === "cancelled";

  return (
    <div className="mx-auto max-w-4xl space-y-4 py-4">
      <div className="grid gap-3 md:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="font-medium">Order ref</span>
          <div className="flex gap-2">
            <Input value={orderRef} onChange={(e) => setOrderRef(e.target.value)} placeholder="ORD-…" />
            <Button type="button" disabled={busy || !orderRef.trim()} onClick={() => void loadOrderReceipts()}>
              Load
            </Button>
          </div>
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Receipt code</span>
          <div className="flex gap-2">
            <Input
              value={receiptCode}
              onChange={(e) => setReceiptCode(e.target.value)}
              placeholder="RCT-…"
            />
            <Button type="button" disabled={busy || !receiptCode.trim()} onClick={() => void loadReceipt(receiptCode.trim())}>
              Open
            </Button>
          </div>
        </label>
      </div>

      {receipts.length > 0 ? (
        <ul className="flex flex-wrap gap-2 text-sm">
          {receipts.map((r) => (
            <li key={r.receipt_code}>
              <button
                type="button"
                className={`rounded border px-2 py-1 ${active?.receipt_code === r.receipt_code ? "border-sky-600 bg-sky-50" : "border-neutral-300"}`}
                onClick={() => void loadReceipt(r.receipt_code)}
              >
                {r.receipt_code} · {r.status}
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}

      {active ? (
        <div className="space-y-3 rounded-lg border border-neutral-200 p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="font-semibold">{active.receipt_code}</p>
              <p className="text-sm text-neutral-600">
                Status {active.status} · prints {active.print_count}
              </p>
            </div>
            <label className="text-sm">
              Format{" "}
              <select
                className="rounded border px-2 py-1"
                value={format}
                onChange={(e) => setFormat(e.target.value as "standard" | "thermal")}
              >
                <option value="standard">Standard</option>
                <option value="thermal">Thermal 80mm</option>
              </select>
            </label>
          </div>

          <div className="flex flex-wrap gap-2">
            <Button type="button" disabled={busy || cancelled} onClick={() => void onPrint(false)}>
              Print
            </Button>
            <Button type="button" variant="outline" disabled={busy || cancelled} onClick={() => void onPrint(true)}>
              Re-print
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={busy || cancelled}
              onClick={() => {
                if (html) openHtmlPrint(html);
              }}
            >
              Preview window
            </Button>
            <a
              className={`inline-flex items-center rounded-md border px-3 py-2 text-sm ${cancelled ? "pointer-events-none opacity-50" : ""}`}
              href={receptionReceiptPdfUrl(active.receipt_code)}
              target="_blank"
              rel="noreferrer"
            >
              PDF
            </a>
          </div>

          {format === "thermal" && thermalText ? (
            <pre className="overflow-auto rounded bg-neutral-950 p-3 text-xs text-neutral-100">{thermalText}</pre>
          ) : null}

          <div
            className="overflow-auto rounded border bg-white p-3"
            dangerouslySetInnerHTML={{ __html: html }}
          />

          <div className="space-y-2 border-t pt-3">
            <label className="block text-sm">
              Cancel reason
              <Input
                className="mt-1"
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                disabled={cancelled}
                placeholder="Optional reason"
              />
            </label>
            <Button type="button" variant="outline" disabled={busy || cancelled} onClick={() => void onCancel()}>
              Cancel receipt
            </Button>
          </div>
        </div>
      ) : (
        <p className="text-sm text-neutral-600">Load an order or receipt to preview and print.</p>
      )}
    </div>
  );
}
