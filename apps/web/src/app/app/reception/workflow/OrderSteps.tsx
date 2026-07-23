"use client";

import { useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  collectReceptionPayment,
  createReceptionOrder,
  fetchReceptionBarcodes,
  fetchReceptionRequestForm,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
  type DuplicateWarning,
  type ReceptionBarcodes,
  type ReceptionOrderCreate,
  type ReceptionPatient,
  type ReceptionTest,
} from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

export type SelectedPatient = {
  patientCode: string;
  patientName: string;
  qrPayload?: string;
};

const PAYMENT_METHODS = ["cash", "transfer", "qr", "pos", "corporate", "insurance"] as const;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function unique<T>(items: T[]): T[] {
  return Array.from(new Set(items));
}

export function PatientStep({
  accessToken,
  organizationId,
  initialQuery,
  onSelect,
}: {
  accessToken: string;
  organizationId?: string | null;
  initialQuery?: string;
  onSelect: (patient: SelectedPatient) => void;
}) {
  const [query, setQuery] = useState(initialQuery ?? "");
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [create, setCreate] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateWarning[]>([]);

  async function runSearch(term = query) {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        { token: accessToken, organizationId },
        term.trim(),
      );
      setPatients(result.items);
    } catch (err) {
      setPatients([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initialQuery?.trim()) {
      void runSearch(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery, accessToken, organizationId]);

  async function submitCreate(force = false) {
    if (!create.full_name.trim() || !create.phone.trim()) {
      setCreateError("Full name and phone are required.");
      return;
    }
    setCreating(true);
    setCreateError(null);
    if (!force) setDuplicates([]);
    try {
      const response = await registerWalkIn(
        { token: accessToken, organizationId },
        {
          full_name: create.full_name.trim(),
          phone: create.phone.trim(),
          national_id: create.national_id.trim() || undefined,
          gender: create.gender.trim() || undefined,
          date_of_birth: create.date_of_birth.trim() || undefined,
          force,
        },
      );
      setDuplicates([]);
      onSelect({
        patientCode: response.patient_code,
        patientName: response.patient.full_name || create.full_name.trim(),
        qrPayload: response.qr_payload ?? response.patient.qr_payload,
      });
    } catch (err) {
      const warnings = getDuplicateWarnings(err);
      if (warnings.length > 0) {
        setDuplicates(warnings);
        setCreateError("Possible duplicate patient. Review matches below or register anyway.");
      } else {
        setCreateError(normalizeApiError(err));
      }
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <SectionHeader
            title="Patient search"
            description="Search by patient code, name, phone, or national ID."
          />
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void runSearch();
            }}
          >
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Patient code, name, phone, or national ID"
            />
            <Button type="submit" disabled={loading}>
              Search
            </Button>
          </form>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={patients.length === 0}
              emptyLabel="No patients found. Register a new patient on the right."
              onRetry={() => void runSearch()}
            >
              <SimpleTable<ReceptionPatient>
                rows={patients}
                rowKey={(row) => row.patient_code}
                columns={[
                  { key: "code", label: "Code", render: (row) => row.patient_code },
                  { key: "name", label: "Name", render: (row) => row.full_name },
                  { key: "phone", label: "Phone", render: (row) => row.phone ?? "—" },
                  { key: "nid", label: "National ID", render: (row) => row.national_id ?? "—" },
                  {
                    key: "action",
                    label: "",
                    render: (row) => (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onSelect({
                            patientCode: row.patient_code,
                            patientName: row.full_name,
                            qrPayload: row.qr_payload,
                          })
                        }
                      >
                        Select
                      </Button>
                    ),
                  },
                ]}
              />
            </DataState>
          ) : (
            <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Search for an existing patient or register a walk-in.
            </p>
          )}
        </div>

        <Card className="space-y-4">
          <SectionHeader title="Create new patient" description="Walk-in registration with duplicate detection." />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="full_name">Full name *</Label>
              <Input
                id="full_name"
                value={create.full_name}
                onChange={(event) => setCreate((prev) => ({ ...prev, full_name: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="phone">Phone *</Label>
              <Input
                id="phone"
                value={create.phone}
                onChange={(event) => setCreate((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="national_id">National ID</Label>
              <Input
                id="national_id"
                value={create.national_id}
                onChange={(event) => setCreate((prev) => ({ ...prev, national_id: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="gender">Gender</Label>
              <Input
                id="gender"
                value={create.gender}
                onChange={(event) => setCreate((prev) => ({ ...prev, gender: event.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="dob">Date of birth</Label>
              <Input
                id="dob"
                type="date"
                value={create.date_of_birth}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, date_of_birth: event.target.value }))
                }
              />
            </div>
          </div>
          {createError ? <p className="text-sm text-rose-600">{createError}</p> : null}
          {duplicates.length > 0 ? (
            <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm font-medium text-amber-900">Duplicate detection</p>
              <ul className="space-y-2 text-sm text-amber-900">
                {duplicates.map((warning, index) => (
                  <li
                    key={`${warning.patient_code ?? warning.field ?? "dup"}-${index}`}
                    className="flex flex-wrap items-center justify-between gap-2"
                  >
                    <span>
                      {String(warning.message ?? warning.reason ?? "Possible match")}
                      {warning.patient_code ? ` (${warning.patient_code})` : ""}
                    </span>
                    {warning.patient_code ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() =>
                          onSelect({
                            patientCode: String(warning.patient_code),
                            patientName: String(warning.full_name ?? warning.patient_code),
                          })
                        }
                      >
                        Use existing
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
              <Button
                variant="secondary"
                disabled={creating}
                onClick={() => void submitCreate(true)}
              >
                {creating ? "Registering…" : "Register anyway"}
              </Button>
            </div>
          ) : null}
          <Button onClick={() => void submitCreate(false)} disabled={creating}>
            {creating ? "Registering…" : "Register & continue"}
          </Button>
        </Card>
      </div>
    </div>
  );
}

export function TestsStep({
  accessToken,
  organizationId,
  patient,
  onOrderCreated,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  onOrderCreated: (orderRef: string, pricing: ReceptionOrderCreate["pricing"]) => void;
}) {
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogQuery, setCatalogQuery] = useState("");
  const [tests, setTests] = useState<ReceptionTest[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedTestIds, setSelectedTestIds] = useState<string[]>([]);
  const [discount, setDiscount] = useState("0");
  const [note, setNote] = useState("");

  const categories = useMemo(
    () => unique(tests.map((test) => test.category).filter(Boolean) as string[]).sort(),
    [tests],
  );
  const categoryToTestIds = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const test of tests) {
      if (!test.category) continue;
      map[test.category] = map[test.category] ?? [];
      map[test.category].push(test.id);
    }
    return map;
  }, [tests]);

  const selectedTests = useMemo(
    () => tests.filter((test) => selectedTestIds.includes(test.id)),
    [tests, selectedTestIds],
  );
  const subtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const total = Math.max(0, subtotal - asFloat(discount));

  async function loadCatalog(q?: string) {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionTests(
        { token: accessToken, organizationId },
        { limit: 100, q: q?.trim() || undefined },
      );
      setTests(result.items);
    } catch (err) {
      setTests([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCatalog();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, organizationId]);

  function toggleCategory(category: string) {
    const ids = categoryToTestIds[category] ?? [];
    const isSelected = selectedCategories.includes(category);
    setSelectedCategories((prev) =>
      isSelected ? prev.filter((value) => value !== category) : [...prev, category],
    );
    setSelectedTestIds((prev) =>
      isSelected ? prev.filter((id) => !ids.includes(id)) : unique([...prev, ...ids]),
    );
  }

  async function submitOrder() {
    setCreating(true);
    setError(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: selectedTestIds,
          discount: asFloat(discount),
          note: note.trim() || undefined,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) throw new Error("Order code not returned by the API.");
      onOrderCreated(orderRef, response.pricing);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests & create order"
        description={`${patient.patientName} · ${patient.patientCode}`}
      />
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void loadCatalog(catalogQuery);
        }}
      >
        <Input
          value={catalogQuery}
          onChange={(event) => setCatalogQuery(event.target.value)}
          placeholder="Search test catalog"
        />
        <Button type="submit" variant="outline" disabled={loading}>
          Search catalog
        </Button>
      </form>
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card className="space-y-3">
            <p className="text-sm font-medium text-slate-900">Test packages</p>
            {categories.length === 0 ? (
              <p className="text-sm text-slate-500">No packages available.</p>
            ) : (
              categories.map((category) => (
                <label
                  key={category}
                  className="flex cursor-pointer items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2 text-sm"
                >
                  <span className="min-w-0 truncate">{category}</span>
                  <input
                    type="checkbox"
                    checked={selectedCategories.includes(category)}
                    onChange={() => toggleCategory(category)}
                  />
                </label>
              ))
            )}
          </Card>

          <div className="space-y-4">
            <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3">
              <div>
                <p className="text-sm text-slate-600">Selected</p>
                <p className="text-lg font-semibold text-slate-900">{selectedTestIds.length} tests</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600">Estimated total</p>
                <p className="font-semibold text-slate-900">{formatCurrency(total)}</p>
                <p className="text-xs text-slate-500">
                  Subtotal {formatCurrency(subtotal)} · Discount {formatCurrency(asFloat(discount))}
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="discount">Discount</Label>
                <Input
                  id="discount"
                  value={discount}
                  onChange={(event) => setDiscount(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="note">Note</Label>
                <Input id="note" value={note} onChange={(event) => setNote(event.target.value)} />
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
                      onChange={() =>
                        setSelectedTestIds((prev) =>
                          prev.includes(row.id)
                            ? prev.filter((id) => id !== row.id)
                            : [...prev, row.id],
                        )
                      }
                    />
                  ),
                },
                { key: "code", label: "Code", render: (row) => row.code },
                { key: "name", label: "Test", render: (row) => row.name },
                { key: "category", label: "Package", render: (row) => row.category ?? "—" },
                {
                  key: "price",
                  label: "Price",
                  render: (row) => (row.price != null ? formatCurrency(row.price) : "—"),
                },
              ]}
            />

            {selectedTests.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {selectedTests.map((test) => (
                  <button
                    key={test.id}
                    type="button"
                    className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-700 hover:border-rose-300 hover:text-rose-700"
                    onClick={() =>
                      setSelectedTestIds((prev) => prev.filter((id) => id !== test.id))
                    }
                  >
                    {test.code} ×
                  </button>
                ))}
              </div>
            ) : null}

            <Button disabled={creating || selectedTestIds.length === 0} onClick={() => void submitOrder()}>
              {creating ? "Creating order…" : "Create order"}
            </Button>
          </div>
        </div>
      </DataState>
    </div>
  );
}

export function FulfillmentStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  onReset,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderCreate["pricing"];
  onReset: () => void;
}) {
  const [paymentStatus, setPaymentStatus] = useState<"pending" | "paid">("pending");
  const [paymentMethod, setPaymentMethod] = useState<string>("cash");
  const [receiptNumber, setReceiptNumber] = useState("");
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [barcodes, setBarcodes] = useState<ReceptionBarcodes | null>(null);
  const [requisitionHtml, setRequisitionHtml] = useState<string | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(false);

  const patientQr =
    barcodes?.patient_qr ?? patient.qrPayload ?? `dxcon:patient:${patient.patientCode}`;

  async function loadDocuments(ref = orderRef, seed?: ReceptionBarcodes) {
    setLoadingDocs(true);
    setError(null);
    try {
      const [codes, form] = await Promise.all([
        seed ? Promise.resolve(seed) : fetchReceptionBarcodes({ token: accessToken, organizationId }, ref),
        fetchReceptionRequestForm({ token: accessToken, organizationId }, ref),
      ]);
      setBarcodes(codes);
      setRequisitionHtml(form.html);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoadingDocs(false);
    }
  }

  async function submitPayment() {
    setPaying(true);
    setError(null);
    try {
      const result = await collectReceptionPayment(
        { token: accessToken, organizationId },
        orderRef,
        {
          payment_method: paymentMethod,
          receipt_number: receiptNumber.trim() || undefined,
        },
      );
      setPaymentStatus("paid");
      await loadDocuments(orderRef, result.barcodes);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setPaying(false);
    }
  }

  function openRequisition() {
    if (!requisitionHtml) return;
    const popup = window.open("", "_blank", "noopener,noreferrer");
    if (!popup) return;
    popup.document.write(requisitionHtml);
    popup.document.close();
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Payment & documents"
        description="Collect payment, then generate barcode, requisition, and patient QR from live order data."
      />

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Patient</p>
          <p className="font-medium text-slate-900">{patient.patientName}</p>
          <p className="text-xs text-slate-500">{patient.patientCode}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Order total</p>
          <p className="font-semibold text-slate-900">{formatCurrency(pricing.total)}</p>
          <p className="text-xs text-slate-500">
            Subtotal {formatCurrency(pricing.subtotal)} · Discount {formatCurrency(pricing.discount)}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Order code</p>
          <p className="break-all font-mono text-sm">{orderRef}</p>
          <p className="text-xs text-slate-500">
            Payment status: {paymentStatus === "paid" ? "paid" : "payment pending"}
          </p>
        </div>
      </div>

      {error ? <p className="text-sm text-rose-600">{error}</p> : null}

      {paymentStatus === "pending" ? (
        <Card className="space-y-4">
          <SectionHeader title="Collect payment" description="Persists payment on the production order." />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="payment_method">Payment method</Label>
              <select
                id="payment_method"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
                value={paymentMethod}
                onChange={(event) => setPaymentMethod(event.target.value)}
              >
                {PAYMENT_METHODS.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="receipt">Receipt number</Label>
              <Input
                id="receipt"
                value={receiptNumber}
                onChange={(event) => setReceiptNumber(event.target.value)}
                placeholder="Optional"
              />
            </div>
          </div>
          <Button disabled={paying} onClick={() => void submitPayment()}>
            {paying ? "Recording payment…" : "Mark paid & generate"}
          </Button>
        </Card>
      ) : (
        <Card className="space-y-4">
          <SectionHeader
            title="Generated documents"
            description="Barcode, requisition, and QR from production APIs."
            actions={
              <Button
                size="sm"
                variant="outline"
                disabled={loadingDocs}
                onClick={() => void loadDocuments()}
              >
                Refresh
              </Button>
            }
          />
          {loadingDocs && !barcodes ? <p className="text-sm text-slate-500">Loading documents…</p> : null}

          {barcodes ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Order barcode</p>
                <p className="font-mono text-sm text-slate-900">{barcodes.order_barcode ?? "—"}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Patient barcode</p>
                <p className="font-mono text-sm text-slate-900">{barcodes.patient_barcode ?? "—"}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3 md:col-span-2">
                <p className="text-xs text-slate-500">Patient QR payload</p>
                <p className="break-all font-mono text-sm text-slate-900">{patientQr}</p>
              </div>
            </div>
          ) : null}

          {barcodes?.sample_barcodes && barcodes.sample_barcodes.length > 0 ? (
            <SimpleTable
              rows={barcodes.sample_barcodes}
              rowKey={(row) => `${row.test_code}-${row.barcode}`}
              columns={[
                { key: "test", label: "Test", render: (row) => row.test_name },
                { key: "code", label: "Code", render: (row) => row.test_code },
                { key: "barcode", label: "Sample barcode", render: (row) => row.barcode },
              ]}
            />
          ) : null}

          <div className="flex flex-wrap gap-3">
            <Button variant="outline" disabled={!requisitionHtml} onClick={openRequisition}>
              Open requisition
            </Button>
            <Button onClick={onReset}>New order</Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export { formatCurrency };
