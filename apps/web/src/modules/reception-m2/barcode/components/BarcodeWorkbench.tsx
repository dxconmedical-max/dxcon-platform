"use client";

import { useCallback, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchReceptionBarcodeLabels,
  previewReceptionBarcodeLabels,
  printReceptionBarcodeLabels,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

const LABEL_OPTIONS = [
  { id: "order", label: "Order barcode" },
  { id: "sample", label: "Sample barcodes" },
  { id: "collection", label: "Collection barcode" },
  { id: "patient", label: "Patient barcode" },
] as const;

function openHtmlPrint(html: string) {
  const popup = window.open("", "_blank", "noopener,noreferrer,width=520,height=720");
  if (!popup) return;
  popup.document.write(html);
  popup.document.close();
}

export function BarcodeWorkbench({ initialOrderRef = "" }: { initialOrderRef?: string }) {
  const { accessToken, activeOrganizationId } = useAuth();
  const ctx = useMemo(
    () => ({ token: accessToken || "", organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const [orderRef, setOrderRef] = useState(initialOrderRef);
  const [selected, setSelected] = useState<string[]>(["order", "sample", "collection"]);
  const [format, setFormat] = useState<"standard" | "thermal">("standard");
  const [printer, setPrinter] = useState<"browser" | "thermal">("browser");
  const [labels, setLabels] = useState<Record<string, unknown>[]>([]);
  const [html, setHtml] = useState("");
  const [thermalText, setThermalText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const toggleType = (id: string) => {
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  };

  const load = useCallback(async () => {
    if (!ctx.token || !orderRef.trim()) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const types = selected.length ? selected : undefined;
      const bundle = await fetchReceptionBarcodeLabels(ctx, orderRef.trim(), types);
      setLabels(Array.isArray(bundle.labels) ? (bundle.labels as Record<string, unknown>[]) : []);
      const preview = await previewReceptionBarcodeLabels(ctx, orderRef.trim(), {
        types,
        format,
      });
      setHtml(preview.html);
      setThermalText(preview.thermal_text);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }, [ctx, orderRef, selected, format]);

  async function onPrint() {
    if (!ctx.token || !orderRef.trim()) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await printReceptionBarcodeLabels(ctx, orderRef.trim(), {
        types: selected,
        format,
        printer: format === "thermal" ? "thermal" : printer,
      });
      setHtml(result.job.html);
      setThermalText(result.job.thermal_text);
      openHtmlPrint(result.job.html);
      setMessage(`Print job ${result.job.job_id} via ${result.job.printer}`);
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
        <div className="flex gap-2">
          <Input
            value={orderRef}
            onChange={(e) => setOrderRef(e.target.value)}
            placeholder="ORD-…"
          />
          <Button type="button" disabled={busy || !orderRef.trim()} onClick={() => void load()}>
            Load labels
          </Button>
        </div>
      </label>

      <div className="flex flex-wrap gap-3 text-sm">
        {LABEL_OPTIONS.map((opt) => (
          <label key={opt.id} className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              checked={selected.includes(opt.id)}
              onChange={() => toggleType(opt.id)}
            />
            {opt.label}
          </label>
        ))}
      </div>

      <div className="flex flex-wrap gap-3 text-sm">
        <label>
          Format{" "}
          <select
            className="rounded border px-2 py-1"
            value={format}
            onChange={(e) => setFormat(e.target.value as "standard" | "thermal")}
          >
            <option value="standard">Standard label</option>
            <option value="thermal">Thermal label 80mm</option>
          </select>
        </label>
        <label>
          Printer{" "}
          <select
            className="rounded border px-2 py-1"
            value={printer}
            onChange={(e) => setPrinter(e.target.value as "browser" | "thermal")}
          >
            <option value="browser">Browser</option>
            <option value="thermal">Thermal adapter</option>
          </select>
        </label>
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {message ? <p className="text-sm text-emerald-700">{message}</p> : null}

      {labels.length > 0 ? (
        <ul className="space-y-2 rounded border p-3 text-sm">
          {labels.map((lab, idx) => (
            <li key={`${String(lab.type)}-${idx}`} className="flex justify-between gap-2 border-b border-dashed py-1 last:border-0">
              <span className="font-medium uppercase">{String(lab.title ?? lab.type)}</span>
              <span className="font-mono text-xs">{lab.code ? String(lab.code) : "— unavailable"}</span>
            </li>
          ))}
        </ul>
      ) : null}

      <div className="flex flex-wrap gap-2">
        <Button type="button" disabled={busy || !html} onClick={() => void onPrint()}>
          Print labels
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={!html}
          onClick={() => openHtmlPrint(html)}
        >
          Preview window
        </Button>
      </div>

      {format === "thermal" && thermalText ? (
        <pre className="overflow-auto rounded bg-neutral-950 p-3 text-xs text-neutral-100">{thermalText}</pre>
      ) : null}

      {html ? (
        <div className="overflow-auto rounded border bg-white p-3" dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <p className="text-sm text-neutral-600">Load a paid order to generate order, sample, and collection labels.</p>
      )}
    </div>
  );
}
