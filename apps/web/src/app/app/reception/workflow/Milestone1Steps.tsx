"use client";

/**
 * Reception Milestone 1 — Patient, catalog, authoritative pricing, order confirmation.
 * Does not implement payment, barcode, QR, requisition, or lab handoff.
 */

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  createReceptionOrder,
  fetchReceptionOrder,
  fetchReceptionTests,
  getOrderCode,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
  type ReceptionTest,
} from "@/lib/api/reception";
import { isRequestAborted, normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";
import { PatientStep, type SelectedPatient } from "./OrderSteps";

const SEARCH_DEBOUNCE_MS = 400;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function uniqueIds(items: string[]): string[] {
  return Array.from(new Set(items.filter(Boolean)));
}

export type CatalogSelection = {
  testIds: string[];
  tests: ReceptionTest[];
  discount: number;
  note: string;
  estimateSubtotal: number;
  estimateTotal: number;
};

export function CatalogSelectStep({
  accessToken,
  organizationId,
  patient,
  initial,
  onContinue,
  onBack,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  initial?: CatalogSelection | null;
  onContinue: (selection: CatalogSelection) => void;
  onBack: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [tests, setTests] = useState<ReceptionTest[]>([]);
  const [selectedTests, setSelectedTests] = useState<ReceptionTest[]>(initial?.tests ?? []);
  const [discount, setDiscount] = useState(String(initial?.discount ?? 0));
  const [note, setNote] = useState(initial?.note ?? "");
  const catalogAbortRef = useRef<AbortController | null>(null);

  const selectedTestIds = useMemo(() => selectedTests.map((test) => test.id), [selectedTests]);
  const estimateSubtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const estimateTotal = Math.max(0, estimateSubtotal - asFloat(discount));

  async function loadCatalog(q?: string) {
    catalogAbortRef.current?.abort();
    const controller = new AbortController();
    catalogAbortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionTests(
        { token: accessToken, organizationId, signal: controller.signal, timeoutMs: 30_000 },
        { limit: 100, q: q?.trim() || undefined },
      );
      if (controller.signal.aborted) return;
      setTests(result.items);
    } catch (err) {
      if (isRequestAborted(err) || controller.signal.aborted) return;
      setTests([]);
      setError(normalizeApiError(err));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadCatalog(catalogQuery);
    }, catalogQuery ? SEARCH_DEBOUNCE_MS : 0);
    return () => {
      window.clearTimeout(timer);
      catalogAbortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [catalogQuery, accessToken, organizationId]);

  function toggleTest(row: ReceptionTest) {
    setSelectedTests((prev) => {
      if (prev.some((test) => test.id === row.id)) {
        return prev.filter((test) => test.id !== row.id);
      }
      return [...prev.filter((test) => test.id !== row.id), row];
    });
  }

  function continueNext() {
    if (selectedTests.length === 0) {
      setError("Select at least one test.");
      return;
    }
    onContinue({
      testIds: uniqueIds(selectedTestIds),
      tests: selectedTests,
      discount: asFloat(discount),
      note: note.trim(),
      estimateSubtotal,
      estimateTotal,
    });
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests"
        description={`${patient.patientName} · ${patient.patientCode}. Catalog prices are display estimates until order creation.`}
        actions={
          <Button size="sm" variant="outline" onClick={onBack}>
            Back
          </Button>
        }
      />
      <Input
        value={catalogQuery}
        onChange={(event) => setCatalogQuery(event.target.value)}
        placeholder="Search test catalog by code or name"
        aria-label="Catalog search"
      />
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="m1-discount">Discount (estimate)</Label>
              <Input
                id="m1-discount"
                value={discount}
                onChange={(event) => setDiscount(event.target.value)}
              />
            </div>
            <div>
              <Label htmlFor="m1-note">Note</Label>
              <Input id="m1-note" value={note} onChange={(event) => setNote(event.target.value)} />
            </div>
          </div>
          <SimpleTable<ReceptionTest>
            rows={tests}
            rowKey={(row) => row.id}
            columns={[
              {
                key: "pick",
                label: "",
                render: (row) => (
                  <input
                    type="checkbox"
                    checked={selectedTestIds.includes(row.id)}
                    onChange={() => toggleTest(row)}
                    aria-label={`Select ${row.code}`}
                  />
                ),
              },
              { key: "code", label: "Code", render: (row) => row.code },
              { key: "name", label: "Test", render: (row) => row.name },
              {
                key: "specimen",
                label: "Specimen",
                render: (row) => row.sample_type ?? "—",
              },
              {
                key: "tat",
                label: "TAT (h)",
                render: (row) =>
                  row.turnaround_hours != null ? String(row.turnaround_hours) : "—",
              },
              {
                key: "price",
                label: "Catalog price",
                render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
              },
            ]}
          />
          {selectedTests.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {selectedTests.map((test) => (
                <Button
                  key={test.id}
                  size="sm"
                  variant="outline"
                  onClick={() => toggleTest(test)}
                  aria-label={`Remove ${test.code}`}
                >
                  {test.code} ×
                </Button>
              ))}
            </div>
          ) : null}
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm">
            <p>
              Selected {selectedTests.length} · Estimate subtotal{" "}
              {formatCurrency(estimateSubtotal)} · Estimate total {formatCurrency(estimateTotal)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Estimate only — final totals come from the order create response.
            </p>
          </div>
          <Button disabled={selectedTests.length === 0} onClick={continueNext}>
            Review pricing
          </Button>
        </div>
      </DataState>
    </div>
  );
}

export function ReviewPricingStep({
  accessToken,
  organizationId,
  patient,
  selection,
  onBack,
  onCreated,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  selection: CatalogSelection;
  onBack: () => void;
  onCreated: (result: {
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  }) => void;
}) {
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [priceDrift, setPriceDrift] = useState<string | null>(null);
  const [pendingResult, setPendingResult] = useState<{
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  } | null>(null);
  const inFlight = useRef(false);

  function acceptCreated(result: {
    orderRef: string;
    pricing: ReceptionOrderPricing;
    order: ReceptionOrderCreate["order"];
    invoice: ReceptionOrderCreate["invoice"];
  }) {
    setPendingResult(null);
    setPriceDrift(null);
    onCreated(result);
  }

  async function submitOrder() {
    if (inFlight.current || pendingResult) return;
    if (!patient.patientCode) {
      setError("Select a patient before creating an order.");
      return;
    }
    if (selection.testIds.length === 0) {
      setError("Select at least one test.");
      return;
    }
    inFlight.current = true;
    setCreating(true);
    setError(null);
    setPriceDrift(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: uniqueIds(selection.testIds),
          discount: selection.discount,
          note: selection.note || undefined,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) {
        throw new Error("Order code not returned by the API.");
      }
      const result = {
        orderRef,
        pricing: response.pricing,
        order: response.order,
        invoice: response.invoice,
      };
      const authoritative = response.pricing.total;
      if (Math.abs(authoritative - selection.estimateTotal) > 0.01) {
        setPendingResult(result);
        setPriceDrift(
          `Backend total ${formatCurrency(authoritative)} differs from estimate ${formatCurrency(selection.estimateTotal)}. Confirm to continue with the backend total.`,
        );
        return;
      }
      acceptCreated(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      inFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Review and pricing"
        description="Confirm selection, then create the laboratory order. Backend pricing is authoritative."
        actions={
          <Button size="sm" variant="outline" disabled={creating} onClick={onBack}>
            Back
          </Button>
        }
      />
      <Card className="space-y-4">
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="font-mono text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Display estimate (not final)</p>
            <p className="font-semibold">{formatCurrency(selection.estimateTotal)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(selection.estimateSubtotal)} · Discount{" "}
              {formatCurrency(selection.discount)}
            </p>
          </div>
        </div>
        <SimpleTable<ReceptionTest>
          rows={selection.tests}
          rowKey={(row) => row.id}
          columns={[
            { key: "code", label: "Code", render: (row) => row.code },
            { key: "name", label: "Test", render: (row) => row.name },
            {
              key: "price",
              label: "Catalog price",
              render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
            },
          ]}
        />
        {selection.note ? (
          <p className="text-sm text-slate-600">
            Note: <span className="text-slate-900">{selection.note}</span>
          </p>
        ) : null}
        {error ? <p className="text-sm text-rose-600">{error}</p> : null}
        {priceDrift && pendingResult ? (
          <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
            <p className="text-sm text-amber-900">{priceDrift}</p>
            <p className="font-mono text-sm text-amber-950">
              Order {pendingResult.orderRef} ·{" "}
              {formatCurrency(pendingResult.pricing.total)}
            </p>
            <Button onClick={() => acceptCreated(pendingResult)}>
              Confirm backend total
            </Button>
          </div>
        ) : null}
        <Button disabled={creating || Boolean(pendingResult)} onClick={() => void submitOrder()}>
          {creating ? "Creating order…" : "Create laboratory order"}
        </Button>
      </Card>
    </div>
  );
}

export function OrderConfirmationStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  order,
  onCreateAnother,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onCreateAnother: () => void;
}) {
  const [detail, setDetail] = useState(order);
  const [authoritative, setAuthoritative] = useState(pricing);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        orderRef,
        { patientCode: patient.patientCode },
      );
      setDetail(result.order);
      setAuthoritative(result.pricing);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refresh();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderRef, accessToken, organizationId]);

  const status = String(detail.status ?? order.status ?? "—");

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Order confirmation"
        description="Backend-issued order number and authoritative pricing. Payment is out of scope for Milestone 1."
        actions={
          <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>
            {loading ? "Refreshing…" : "Refresh"}
          </Button>
        }
      />
      <Card className="space-y-4">
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3">
          <p className="text-xs font-medium uppercase tracking-wide text-emerald-700">
            Laboratory order number
          </p>
          <p className="mt-1 break-all font-mono text-lg font-semibold text-emerald-950">
            {orderRef}
          </p>
        </div>
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void refresh()}>
              Retry
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Patient</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="font-mono text-xs">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Status</p>
            <p className="font-medium uppercase">{status}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Authoritative total</p>
            <p className="font-semibold">{formatCurrency(authoritative.total)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(authoritative.subtotal)} · Discount{" "}
              {formatCurrency(authoritative.discount)}
              {authoritative.tax != null ? ` · Tax ${formatCurrency(authoritative.tax)}` : ""}
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3">
          <a href={`/app/reception/workflow?order=${encodeURIComponent(orderRef)}`}>
            <Button variant="outline">Open order</Button>
          </a>
          <Button onClick={onCreateAnother}>Create another order</Button>
        </div>
      </Card>
    </div>
  );
}

// Re-export PatientStep for workflow composition
export { PatientStep };
export type { SelectedPatient };
