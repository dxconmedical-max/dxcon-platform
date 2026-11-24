"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  REJECTION_REASON_OPTIONS,
  assignBench,
  createAccession,
  enterLabResult,
  fetchLabOrder,
  fetchTestingQueue,
  medicalValidate,
  medicalReject,
  medicalReopen,
  passQc,
  receiveSpecimen,
  rejectSpecimen,
  releaseLabResult,
  startProcessing,
  technicalValidate,
  verifyLabIdentifiers,
  type LabOrderWorkspace,
  type LabQueueRow,
} from "@/lib/api/labWorkflow";

import { DataState, SectionHeader, StatusPill } from "../_components/ui";

const STEPS = ["Receive", "Accession", "Process", "Results", "Validate"] as const;

function LabWorkflowPanel() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const searchParams = useSearchParams();
  const orderParam = searchParams.get("order");

  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const canWrite = ["LAB", "LAB_TECHNICIAN", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(
    role ?? "",
  );
  const canTechValidate = ["LAB", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");
  const canMedical = ["DOCTOR", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const [queue, setQueue] = useState<LabQueueRow[]>([]);
  const [selectedOrder, setSelectedOrder] = useState<string | null>(orderParam);
  const [detail, setDetail] = useState<LabOrderWorkspace | null>(null);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const [sampleCode, setSampleCode] = useState("");
  const [barcode, setBarcode] = useState("");
  const [patientCode, setPatientCode] = useState("");
  const [rejectReason, setRejectReason] = useState("hemolyzed");
  const [rejectNote, setRejectNote] = useState("");
  const [benchId, setBenchId] = useState("BENCH-CHEM-1");
  const [instrumentId, setInstrumentId] = useState("ANALYZER-01");
  const [technician, setTechnician] = useState("");
  const [testCode, setTestCode] = useState("");
  const [resultValue, setResultValue] = useState("");
  const [unit, setUnit] = useState("");
  const [referenceRange, setReferenceRange] = useState("");
  const [criticalLow, setCriticalLow] = useState("");
  const [criticalHigh, setCriticalHigh] = useState("");
  const [doctorNote, setDoctorNote] = useState("");

  const refreshDetail = useCallback(
    async (orderCode: string) => {
      const ws = await fetchLabOrder(auth, orderCode);
      setDetail(ws);
      const order = ws.order as { status?: string; patient_code?: string; items?: Array<{ test_code?: string }> };
      const collection = ws.collection as {
        sample_code?: string;
        barcode_value?: string;
        condition_status?: string;
      } | null;
      const accession = ws.accession as {
        processing_status?: string;
        bench_id?: string;
        instrument_id?: string;
        technician?: string;
      } | null;

      setSampleCode(collection?.sample_code || "");
      setBarcode(collection?.barcode_value || "");
      setPatientCode(order.patient_code || "");
      setBenchId(accession?.bench_id || "BENCH-CHEM-1");
      setInstrumentId(accession?.instrument_id || "ANALYZER-01");
      setTechnician(accession?.technician || "");
      setTestCode(order.items?.[0]?.test_code || testCode);

      const status = order.status || "";
      const proc = accession?.processing_status || "";
      if (status === "approved" || proc === "medically_validated") setStep(4);
      else if (status === "pending_review" || proc === "tech_validated") setStep(4);
      else if (status === "testing" || proc === "results_entered" || proc === "processing") setStep(3);
      else if (ws.accession) setStep(2);
      else if (status === "lab_received") setStep(1);
      else setStep(0);
      return ws;
    },
    [auth, testCode],
  );

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const q = await fetchTestingQueue(auth, { per_page: 40 });
      const unique = new Map<string, LabQueueRow>();
      for (const row of q.data) {
        if (!unique.has(row.order_code)) unique.set(row.order_code, row);
      }
      const items = Array.from(unique.values());
      setQueue(items);
      const target = selectedOrder || orderParam || items[0]?.order_code || null;
      setSelectedOrder(target);
      if (target) await refreshDetail(target);
      else setDetail(null);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth, orderParam, refreshDetail, selectedOrder]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, orderParam]);

  async function run(action: () => Promise<unknown>, okMsg: string, nextStep?: number) {
    if (!selectedOrder) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(okMsg);
      await refreshDetail(selectedOrder);
      await load();
      if (nextStep !== undefined) setStep(nextStep);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const orderStatus = String((detail?.order as { status?: string } | undefined)?.status || "—");
  const accessionNumber = String(
    (detail?.accession as { accession_number?: string } | null | undefined)?.accession_number || "—",
  );

  return (
    <div className="space-y-6 p-4 md:p-6">
      <SectionHeader
        title="Quy trình xét nghiệm"
        description="Nhận mẫu → cấp mã số → xử lý → kết quả → duyệt kỹ thuật và duyệt chuyên môn."
        actions={
          <>
            <Link href="/app/lab/queue">
              <Button size="sm" variant="outline">
                Hàng đợi
              </Button>
            </Link>
            <Button size="sm" variant="outline" onClick={() => void load()} disabled={busy}>
              Làm mới
            </Button>
          </>
        }
      />

      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, idx) => (
          <button
            key={label}
            type="button"
            className={`rounded-md border px-3 py-1.5 text-sm ${
              idx === step
                ? "border-slate-900 bg-slate-900 text-white"
                : idx < step
                  ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                  : "border-slate-200 bg-white text-slate-600"
            }`}
            onClick={() => setStep(idx)}
          >
            {idx + 1}. {label}
          </button>
        ))}
      </div>

      {message ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
        </p>
      ) : null}

      <DataState
        loading={loading}
        error={error}
        empty={!detail && !queue.length}
        emptyLabel="Chưa có việc nào ở phòng xét nghiệm. Hãy hoàn tất bàn giao thu mẫu trước."
        onRetry={() => void load()}
      >
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Đơn</p>
            {queue.map((row) => (
              <button
                key={row.order_code}
                type="button"
                className={`block w-full rounded-lg border px-3 py-2 text-left text-sm ${
                  selectedOrder === row.order_code
                    ? "border-slate-900 bg-slate-900 text-white"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }`}
                onClick={() => {
                  setSelectedOrder(row.order_code);
                  void refreshDetail(row.order_code);
                }}
              >
                <div className="font-medium">{row.order_code}</div>
                <div className="opacity-80">{row.patient || row.patient_name}</div>
              </button>
            ))}
          </aside>

          <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
            <div className="flex flex-wrap items-center gap-3">
              <h3 className="text-base font-semibold text-slate-900">{selectedOrder}</h3>
              <StatusPill status={orderStatus} />
              <span className="text-sm text-slate-500">Accession {accessionNumber}</span>
              {detail?.locked ? <StatusPill status="locked" /> : null}
            </div>

            {step === 0 ? (
              <div className="space-y-3">
                <Field label="Mã mẫu" value={sampleCode} onChange={setSampleCode} />
                <Field label="Mã vạch" value={barcode} onChange={setBarcode} />
                <Field label="Mã bệnh nhân" value={patientCode} onChange={setPatientCode} />
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () =>
                          verifyLabIdentifiers(auth, {
                            order_code: selectedOrder!,
                            sample_code: sampleCode || undefined,
                            barcode_value: barcode || undefined,
                            patient_code: patientCode || undefined,
                          }),
                        "Đã xác minh định danh.",
                      )
                    }
                  >
                    Xác minh định danh
                  </Button>
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () =>
                          receiveSpecimen(auth, {
                            order_code: selectedOrder!,
                            sample_code: sampleCode || undefined,
                            barcode_value: barcode || undefined,
                            patient_code: patientCode || undefined,
                            condition_status: "acceptable",
                          }),
                        "Đã nhận mẫu.",
                      )
                    }
                  >
                    Chấp nhận và nhận mẫu
                  </Button>
                </div>
                <div className="rounded-lg border border-rose-100 bg-rose-50/50 p-3">
                  <p className="mb-2 text-sm font-medium text-rose-900">Từ chối mẫu</p>
                  <select
                    className="mb-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                    value={rejectReason}
                    onChange={(e) => setRejectReason(e.target.value)}
                  >
                    {REJECTION_REASON_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  <textarea
                    className="mb-2 w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                    rows={2}
                    placeholder="Ghi chú"
                    value={rejectNote}
                    onChange={(e) => setRejectNote(e.target.value)}
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () =>
                          rejectSpecimen(auth, {
                            order_code: selectedOrder!,
                            sample_code: sampleCode || undefined,
                            rejection_reason: rejectReason,
                            note: rejectNote || rejectReason,
                          }),
                        "Đã từ chối mẫu.",
                      )
                    }
                  >
                    Từ chối
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 1 ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">
                  Tạo mã số mẫu theo định dạng ACC-YYYYMMDD-000001.
                </p>
                <Button
                  size="sm"
                  disabled={!canWrite || busy || !selectedOrder}
                  onClick={() =>
                    void run(
                      () => createAccession(auth, { order_code: selectedOrder!, sample_code: sampleCode || undefined }),
                      "Accessioned.",
                    )
                  }
                >
                  Cấp mã số mẫu
                </Button>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-3">
                <Field label="Bàn xét nghiệm" value={benchId} onChange={setBenchId} />
                <Field label="Máy xét nghiệm" value={instrumentId} onChange={setInstrumentId} />
                <Field label="Kỹ thuật viên" value={technician} onChange={setTechnician} />
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () =>
                          assignBench(auth, {
                            order_code: selectedOrder!,
                            bench_id: benchId,
                            instrument_id: instrumentId,
                            technician: technician || undefined,
                          }),
                        "Assigned.",
                      )
                    }
                  >
                    Phân công
                  </Button>
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => startProcessing(auth, selectedOrder!), "Đã bắt đầu xử lý.")
                    }
                  >
                    Bắt đầu xử lý
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="space-y-3">
                <Field label="Mã xét nghiệm" value={testCode} onChange={setTestCode} />
                <Field label="Giá trị kết quả" value={resultValue} onChange={setResultValue} />
                <Field label="Unit (để trống = tự điền)" value={unit} onChange={setUnit} />
                <Field label="Reference range (để trống = tự điền theo khoảng DxCon)" value={referenceRange} onChange={setReferenceRange} />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Nguy kịch thấp" value={criticalLow} onChange={setCriticalLow} />
                  <Field label="Nguy kịch cao" value={criticalHigh} onChange={setCriticalHigh} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder || detail?.locked}
                    onClick={() =>
                      void run(
                        () =>
                          enterLabResult(auth, {
                            order_code: selectedOrder!,
                            test_code: testCode,
                            result_value: resultValue,
                            unit: unit || undefined,
                            reference_range: referenceRange || undefined,
                            critical_low: criticalLow ? Number(criticalLow) : undefined,
                            critical_high: criticalHigh ? Number(criticalHigh) : undefined,
                            instrument: instrumentId,
                            technician: technician || undefined,
                          }),
                        "Đã nhập kết quả.",
                      )
                    }
                  >
                    Nhập kết quả
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canWrite || busy || !selectedOrder || detail?.locked}
                    onClick={() =>
                      void run(() => passQc(auth, selectedOrder!), "QC passed. Tiếp theo: Technical validate.", 4)
                    }
                  >
                    QC đạt
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 4 ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">
                  Duyệt kỹ thuật sẽ khóa kết quả. Duyệt chuyên môn là bác sĩ ký xác nhận.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={!canTechValidate || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => technicalValidate(auth, selectedOrder!), "Đã duyệt kỹ thuật.")
                    }
                  >
                    Duyệt kỹ thuật
                  </Button>
                </div>
                <textarea
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                  rows={2}
                  placeholder="Ghi chú của bác sĩ"
                  value={doctorNote}
                  onChange={(e) => setDoctorNote(e.target.value)}
                />
                <Button
                  size="sm"
                  disabled={!canMedical || busy || !selectedOrder}
                  onClick={() =>
                    void run(
                      () => medicalValidate(auth, selectedOrder!, doctorNote || undefined),
                      "Đã duyệt chuyên môn.",
                    )
                  }
                >
                  Duyệt chuyên môn
                </Button>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () => medicalReject(auth, selectedOrder!, doctorNote || undefined),
                        "Đã ghi nhận từ chối chuyên môn.",
                      )
                    }
                  >
                    Từ chối chuyên môn
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () => medicalReopen(auth, selectedOrder!, doctorNote || undefined),
                        "Đã mở lại duyệt chuyên môn.",
                      )
                    }
                  >
                    Mở lại
                  </Button>
                  <Button
                    size="sm"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => releaseLabResult(auth, selectedOrder!), "Đã trả kết quả.")
                    }
                  >
                    Trả kết quả
                  </Button>
                  <Link
                    href="/app/lab/release"
                    className="self-center text-sm text-sky-700 hover:underline"
                  >
                    Bảng trả kết quả
                  </Link>
                </div>
              </div>
            ) : null}

            {detail?.result ? (
              <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p className="font-medium text-slate-900">Kết quả hiện tại</p>
                <pre className="mt-2 overflow-x-auto text-xs">
                  {JSON.stringify(detail.result, null, 2)}
                </pre>
              </div>
            ) : null}
          </section>
        </div>
      </DataState>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-slate-600">{label}</span>
      <input
        className="w-full rounded-md border border-slate-200 px-3 py-2"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

export default function LabWorkflowPage() {
  return (
    <AppShell title="Quy trình xét nghiệm" workspacePath="/app/lab">
      <Suspense fallback={<p className="p-6 text-sm text-slate-500">Đang tải quy trình…</p>}>
        <LabWorkflowPanel />
      </Suspense>
    </AppShell>
  );
}
