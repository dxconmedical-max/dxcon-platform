"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { SectionHeader } from "@/components/workspace/primitives";
import {
  approveResult,
  collectSample,
  completeQc,
  createOrder,
  createPatient,
  downloadHtmlReport,
  enterResults,
  fetchCatalog,
  fetchReport,
  getOrder,
  markInTransit,
  payOrder,
  receiveAtLab,
  releaseResult,
  scheduleCollection,
  searchPatients,
  type CatalogTest,
  type WorkflowOrder,
  type WorkflowPatient,
} from "@/lib/api/diagnostic-workflow";
import { normalizeApiError } from "@/lib/errors";

const MILESTONES = [
  "ORDERED",
  "COLLECTION_SCHEDULED",
  "COLLECTED",
  "IN_TRANSIT",
  "RECEIVED_AT_LAB",
  "PROCESSING",
  "APPROVED",
  "RELEASED",
] as const;

type StepKey =
  | "patient"
  | "order"
  | "pay"
  | "collection"
  | "collect"
  | "transit"
  | "receive"
  | "results"
  | "qc"
  | "approve"
  | "release"
  | "report";

function WorkflowPanel({ accessToken, organizationId }: WorkspaceContext) {
  const ctx = useMemo(
    () => ({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );

  const [catalog, setCatalog] = useState<CatalogTest[]>([]);
  const [selectedTests, setSelectedTests] = useState<string[]>([]);
  const [patientQuery, setPatientQuery] = useState("");
  const [patients, setPatients] = useState<WorkflowPatient[]>([]);
  const [patient, setPatient] = useState<WorkflowPatient | null>(null);
  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [order, setOrder] = useState<WorkflowOrder | null>(null);
  const [busy, setBusy] = useState<StepKey | null>(null);
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    setLoadingCatalog(true);
    setError(null);
    try {
      const items = await fetchCatalog(ctx);
      setCatalog(items);
      if (items[0]?.id) setSelectedTests([String(items[0].id)]);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoadingCatalog(false);
    }
  }, [ctx]);

  useEffect(() => {
    void loadCatalog();
  }, [loadCatalog]);

  async function runStep<T>(key: StepKey, action: () => Promise<T>): Promise<T | null> {
    setBusy(key);
    setError(null);
    setInfo(null);
    try {
      return await action();
    } catch (err) {
      setError(normalizeApiError(err));
      return null;
    } finally {
      setBusy(null);
    }
  }

  async function onSearchPatients() {
    const rows = await runStep("patient", () => searchPatients(ctx, patientQuery.trim()));
    if (rows) setPatients(rows);
  }

  async function onCreatePatient() {
    const created = await runStep("patient", () =>
      createPatient(ctx, { full_name: newName.trim(), phone: newPhone.trim() || undefined }),
    );
    if (created) {
      setPatient(created);
      setInfo(`Patient ${created.patient_code} created.`);
      setNewName("");
      setNewPhone("");
    }
  }

  async function onCreateOrder() {
    if (!patient) {
      setError("Select or create a patient first.");
      return;
    }
    if (selectedTests.length === 0) {
      setError("Select at least one catalog test.");
      return;
    }
    const created = await runStep("order", () =>
      createOrder(ctx, {
        patient_code: patient.patient_code,
        test_catalog_ids: selectedTests,
      }),
    );
    if (created) {
      setOrder(created);
      setInfo(`Order ${created.order_code} created (${created.milestone}).`);
    }
  }

  async function advance(
    key: StepKey,
    fn: (c: typeof ctx, ref: string) => Promise<WorkflowOrder>,
    message: string,
  ) {
    if (!order?.order_code) {
      setError("Create an order first.");
      return;
    }
    const next = await runStep(key, () => fn(ctx, order.order_code));
    if (next) {
      setOrder(next);
      setInfo(`${message} → ${next.milestone ?? next.status}`);
    }
  }

  async function onDownloadReport() {
    if (!order?.order_code) return;
    const report = await runStep("report", () => fetchReport(ctx, order.order_code));
    if (report?.html) {
      downloadHtmlReport(report.html, report.filename || `${order.order_code}-report.html`);
      setInfo("Report downloaded.");
    }
  }

  async function onRefresh() {
    if (!order?.order_code) return;
    const latest = await runStep("order", () => getOrder(ctx, order.order_code));
    if (latest) setOrder(latest);
  }

  function toggleTest(id: string) {
    setSelectedTests((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    );
  }

  const milestone = order?.milestone ?? null;

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Diagnostic order workflow"
        description="End-to-end live path: patient → order → specimen milestones → result → release → report. No sample data."
      />

      {error ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" role="alert">
          {error}
        </div>
      ) : null}
      {info ? (
        <Card className="border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-900">{info}</Card>
      ) : null}

      <Card className="space-y-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-slate-700">Milestone</span>
          {MILESTONES.map((m) => (
            <Badge
              key={m}
              className={
                milestone === m
                  ? "bg-teal-600 text-white"
                  : "bg-slate-100 text-slate-600"
              }
            >
              {m}
            </Badge>
          ))}
        </div>
        {order ? (
          <div className="flex flex-wrap items-center gap-3 text-sm text-slate-700">
            <span>
              Order <strong>{order.order_code}</strong>
            </span>
            <span>Status: {order.status}</span>
            {order.barcode_value ? <span>Barcode: {order.barcode_value}</span> : null}
            <Button size="sm" variant="outline" onClick={onRefresh} disabled={busy !== null}>
              Refresh
            </Button>
          </div>
        ) : (
          <p className="text-sm text-slate-500">No order yet — create a patient and order below.</p>
        )}
      </Card>

      <Card className="space-y-4 p-4">
        <h3 className="font-semibold text-slate-900">1. Patient</h3>
        <div className="grid gap-3 md:grid-cols-3">
          <div className="md:col-span-2">
            <Label htmlFor="pq">Search existing</Label>
            <div className="flex gap-2">
              <Input
                id="pq"
                value={patientQuery}
                onChange={(e) => setPatientQuery(e.target.value)}
                placeholder="Name or phone"
              />
              <Button variant="outline" onClick={onSearchPatients} disabled={busy !== null}>
                Search
              </Button>
            </div>
          </div>
        </div>
        {patients.length === 0 && patientQuery ? (
          <p className="text-sm text-slate-500">No patients matched.</p>
        ) : null}
        {patients.length > 0 ? (
          <ul className="divide-y divide-slate-100 rounded-lg border border-slate-200">
            {patients.map((p) => (
              <li key={p.patient_code} className="flex items-center justify-between px-3 py-2 text-sm">
                <span>
                  {p.full_name} · {p.patient_code} · {p.phone || "—"}
                </span>
                <Button size="sm" variant="outline" onClick={() => setPatient(p)}>
                  Select
                </Button>
              </li>
            ))}
          </ul>
        ) : null}
        <div className="grid gap-3 border-t border-slate-100 pt-4 md:grid-cols-3">
          <div>
            <Label htmlFor="nn">New patient name</Label>
            <Input id="nn" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <div>
            <Label htmlFor="np">Phone</Label>
            <Input id="np" value={newPhone} onChange={(e) => setNewPhone(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Button
              onClick={onCreatePatient}
              disabled={busy !== null || newName.trim().length < 2}
            >
              {busy === "patient" ? "Saving…" : "Create patient"}
            </Button>
          </div>
        </div>
        {patient ? (
          <p className="text-sm text-teal-800">
            Selected: <strong>{patient.full_name}</strong> ({patient.patient_code})
          </p>
        ) : null}
      </Card>

      <Card className="space-y-4 p-4">
        <h3 className="font-semibold text-slate-900">2. Order + catalog tests</h3>
        {loadingCatalog ? (
          <p className="text-sm text-slate-500">Loading catalog…</p>
        ) : catalog.length === 0 ? (
          <p className="text-sm text-slate-500">Catalog empty — seed failed or unavailable.</p>
        ) : (
          <ul className="grid gap-2 md:grid-cols-2">
            {catalog.slice(0, 12).map((test) => {
              const id = String(test.id ?? "");
              const checked = selectedTests.includes(id);
              return (
                <li key={id}>
                  <label className="flex cursor-pointer items-start gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm hover:border-teal-400">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleTest(id)}
                      className="mt-1"
                    />
                    <span>
                      <span className="font-medium">{test.name}</span>
                      <span className="block text-slate-500">
                        {test.code} · {test.price ?? 0}
                      </span>
                    </span>
                  </label>
                </li>
              );
            })}
          </ul>
        )}
        <Button onClick={onCreateOrder} disabled={busy !== null || !patient}>
          {busy === "order" ? "Creating…" : "Create order"}
        </Button>
      </Card>

      <Card className="space-y-3 p-4">
        <h3 className="font-semibold text-slate-900">3. Specimen lifecycle</h3>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("pay", payOrder, "Paid")}
          >
            {busy === "pay" ? "…" : "Mark paid"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("collection", scheduleCollection, "Collection scheduled")}
          >
            {busy === "collection" ? "…" : "Schedule collection"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("collect", collectSample, "Collected")}
          >
            {busy === "collect" ? "…" : "Collect"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("transit", markInTransit, "In transit")}
          >
            {busy === "transit" ? "…" : "In transit"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("receive", receiveAtLab, "Received at lab")}
          >
            {busy === "receive" ? "…" : "Receive at lab"}
          </Button>
        </div>
      </Card>

      <Card className="space-y-3 p-4">
        <h3 className="font-semibold text-slate-900">4. Results → release → report</h3>
        <div className="flex flex-wrap gap-2">
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("results", enterResults, "Results entered")}
          >
            {busy === "results" ? "…" : "Enter results"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("qc", completeQc, "QC complete")}
          >
            {busy === "qc" ? "…" : "Complete QC"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() =>
              advance("approve", (c, ref) => approveResult(c, ref), "Approved")
            }
          >
            {busy === "approve" ? "…" : "Approve"}
          </Button>
          <Button
            size="sm"
            disabled={!order || busy !== null}
            onClick={() => advance("release", releaseResult, "Released")}
          >
            {busy === "release" ? "…" : "Release"}
          </Button>
          <Button
            size="sm"
            variant="secondary"
            disabled={!order || busy !== null || order?.milestone !== "RELEASED"}
            onClick={onDownloadReport}
          >
            {busy === "report" ? "…" : "Download report"}
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function AdminDiagnosticWorkflowPage() {
  return (
    <WorkspaceScreen
      title="Diagnostic workflow"
      workspacePath="/app/admin"
      permission="users.read"
    >
      {(ctx) => <WorkflowPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
