"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { normalizeApiError } from "@/lib/errors";
import type { BulkPriceResult } from "@/lib/api/clinicBilling";

type Props = {
  heading: string;
  priceWord: string; // e.g. "giá bán" / "giá nhập"
  onPaste: (text: string, apply: boolean) => Promise<BulkPriceResult>;
  onFile: (file: File, apply: boolean) => Promise<BulkPriceResult>;
  onTemplate: () => Promise<void>;
  onApplied: () => Promise<void> | void;
};

const INPUT = "rounded-lg border border-slate-300 px-3 py-1.5 text-sm";

export function PriceSheetPanel({ heading, priceWord, onPaste, onFile, onTemplate, onApplied }: Props) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<BulkPriceResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(fn: () => Promise<BulkPriceResult>, apply: boolean) {
    setBusy(true);
    setError(null);
    try {
      const r = await fn();
      setResult(r);
      if (apply) {
        if (r.errors.length === 0) {
          setText("");
          setFile(null);
          if (fileRef.current) fileRef.current.value = "";
        }
        await onApplied();
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const useFile = file !== null;
  const canRun = useFile || text.trim().length > 0;
  const go = (apply: boolean) => run(() => (file ? onFile(file, apply) : onPaste(text, apply)), apply);

  return (
    <div className="space-y-3 rounded-lg bg-slate-50 p-3">
      <p className="text-sm font-medium">{heading}</p>
      <div className="space-y-1">
        <p className="text-xs font-medium text-slate-700">Cách 1: dùng biểu mẫu Excel (nên dùng khi có nhiều mã)</p>
        <ol className="list-decimal space-y-0.5 pl-5 text-xs text-slate-600">
          <li>Bấm “Tải biểu mẫu” để lấy file có sẵn toàn bộ mã và tên xét nghiệm.</li>
          <li>Điền {priceWord} vào cột cuối. Để trống thì giữ nguyên, ghi “-” thì xóa giá.</li>
          <li>Chọn file đã điền, bấm “Kiểm tra” rồi “Áp dụng”.</li>
        </ol>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            disabled={busy}
            onClick={async () => {
              setError(null);
              try {
                await onTemplate();
              } catch (err) {
                setError(normalizeApiError(err));
              }
            }}
          >
            Tải biểu mẫu
          </Button>
          <input
            ref={fileRef}
            type="file"
            accept=".xlsx,.xlsm,.csv,.txt"
            aria-label="Chọn file biểu mẫu đã điền"
            className="text-xs"
            onChange={(e) => {
              setFile(e.target.files?.[0] ?? null);
              setResult(null);
            }}
          />
        </div>
      </div>
      <div className="space-y-1">
        <p className="text-xs font-medium text-slate-700">Cách 2: dán danh sách (ít mã)</p>
        <textarea
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            setResult(null);
          }}
          rows={4}
          disabled={useFile}
          placeholder={"CBC\t120000\nHBA1C\t250000"}
          aria-label="Danh sách mã và giá"
          className={`${INPUT} w-full font-mono`}
        />
        <p className="text-xs text-slate-500">Mỗi dòng: mã rồi giá, cách nhau bằng dấu cách, dấu ; hoặc dán thẳng hai cột từ Excel.</p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button size="sm" variant="outline" disabled={busy || !canRun} onClick={() => void go(false)}>
          Kiểm tra
        </Button>
        <Button size="sm" disabled={busy || !canRun} onClick={() => void go(true)}>
          Áp dụng
        </Button>
      </div>
      {error ? <p role="alert" className="text-sm text-red-700">{error}</p> : null}
      {result ? (
        <div className="text-sm">
          <p>
            {result.applied ? "Đã áp dụng" : "Kiểm tra xong (chưa lưu)"}: thêm mới {result.created}, cập nhật {result.updated}, xóa {result.removed}
            {result.errors.length ? `, ${result.errors.length} dòng lỗi` : ""}.
          </p>
          {result.errors.length ? (
            <ul className="mt-1 max-h-40 list-disc overflow-auto pl-5 text-xs text-red-700">
              {result.errors.slice(0, 50).map((e) => (
                <li key={`${e.line}-${e.code}`}>
                  Dòng {e.line} ({e.code}): {e.error}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
