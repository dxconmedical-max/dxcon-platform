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
  const [referenceRange, setReferenceRange] = useState("3.5-5.5");
  const [criticalLow, setCriticalLow] = useState("2");
  const [criticalHigh, setCriticalHigh] = useState("8");
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

  async function run(action: () => Promise<unknown>, okMsg: string) {
    if (!selectedOrder) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await action();
      setMessage(okMsg);
      await refreshDetail(selectedOrder);
      await load();
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
        title="Laboratory workflow"
        description="Receive → accession → process → results → technical & medical validation."
        actions={
          <>
            <Link href="/app/lab/queue">
              <Button size="sm" variant="outline">
                Queue
              </Button>
            </Link>
            <Button size="sm" variant="outline" onClick={() => void load()} disabled={busy}>
              Refresh
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
        emptyLabel="No laboratory work items. Complete Sample Collection handoff first."
        onRetry={() => void load()}
      >
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">Orders</p>
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
                <Field label="Sample code" value={sampleCode} onChange={setSampleCode} />
                <Field label="Barcode" value={barcode} onChange={setBarcode} />
                <Field label="Patient code" value={patientCode} onChange={setPatientCode} />
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
                        "Identifiers verified.",
                      )
                    }
                  >
                    Verify identifiers
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
                        "Specimen received.",
                      )
                    }
                  >
                    Accept & receive
                  </Button>
                </div>
                <div className="rounded-lg border border-rose-100 bg-rose-50/50 p-3">
                  <p className="mb-2 text-sm font-medium text-rose-900">Reject specimen</p>
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
                    placeholder="Notes"
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
                        "Specimen rejected.",
                      )
                    }
                  >
                    Reject
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 1 ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">
                  Generate synthetic accession ID in format ACC-YYYYMMDD-000001.
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
                  Create accession
                </Button>
              </div>
            ) : null}

            {step === 2 ? (
              <div className="space-y-3">
                <Field label="Bench" value={benchId} onChange={setBenchId} />
                <Field label="Instrument" value={instrumentId} onChange={setInstrumentId} />
                <Field label="Technician" value={technician} onChange={setTechnician} />
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
                    Assign
                  </Button>
                  <Button
                    size="sm"
                    disabled={!canWrite || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => startProcessing(auth, selectedOrder!), "Processing started.")
                    }
                  >
                    Start processing
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 3 ? (
              <div className="space-y-3">
                <Field label="Test code" value={testCode} onChange={setTestCode} />
                <Field label="Result value" value={resultValue} onChange={setResultValue} />
                <Field label="Unit" value={unit} onChange={setUnit} />
                <Field label="Reference range" value={referenceRange} onChange={setReferenceRange} />
                <div className="grid gap-3 sm:grid-cols-2">
                  <Field label="Critical low" value={criticalLow} onChange={setCriticalLow} />
                  <Field label="Critical high" value={criticalHigh} onChange={setCriticalHigh} />
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
                        "Result entered.",
                      )
                    }
                  >
                    Enter result
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canWrite || busy || !selectedOrder || detail?.locked}
                    onClick={() =>
                      void run(() => passQc(auth, selectedOrder!), "QC passed.")
                    }
                  >
                    QC pass
                  </Button>
                </div>
              </div>
            ) : null}

            {step === 4 ? (
              <div className="space-y-3">
                <p className="text-sm text-slate-600">
                  Technical validation locks results. Medical validation is doctor sign-off.
                </p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    disabled={!canTechValidate || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => technicalValidate(auth, selectedOrder!), "Technical validation complete.")
                    }
                  >
                    Technical validate
                  </Button>
                </div>
                <textarea
                  className="w-full rounded-md border border-slate-200 px-3 py-2 text-sm"
                  rows={2}
                  placeholder="Doctor note"
                  value={doctorNote}
                  onChange={(e) => setDoctorNote(e.target.value)}
                />
                <Button
                  size="sm"
                  disabled={!canMedical || busy || !selectedOrder}
                  onClick={() =>
                    void run(
                      () => medicalValidate(auth, selectedOrder!, doctorNote || undefined),
                      "Medical validation complete.",
                    )
                  }
                >
                  Medical validate
                </Button>
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () => medicalReject(auth, selectedOrder!, doctorNote || undefined),
                        "Medical rejection recorded.",
                      )
                    }
                  >
                    Medical reject
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(
                        () => medicalReopen(auth, selectedOrder!, doctorNote || undefined),
                        "Medical validation reopened.",
                      )
                    }
                  >
                    Reopen
                  </Button>
                  <Button
                    size="sm"
                    disabled={!canMedical || busy || !selectedOrder}
                    onClick={() =>
                      void run(() => releaseLabResult(auth, selectedOrder!), "Result released.")
                    }
                  >
                    Release result
                  </Button>
                  <Link
                    href="/app/lab/release"
                    className="self-center text-sm text-sky-700 hover:underline"
                  >
                    Release board
                  </Link>
                </div>
              </div>
            ) : null}

            {detail?.result ? (
              <div className="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm text-slate-700">
                <p className="font-medium text-slate-900">Current result</p>
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
    <AppShell title="Lab workflow" workspacePath="/app/lab">
      <Suspense fallback={<p className="p-6 text-sm text-slate-500">Loading workflow…</p>}>
        <LabWorkflowPanel />
      </Suspense>
    </AppShell>
  );
}
