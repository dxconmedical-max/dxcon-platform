"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  createReceptionOrder,
  fetchReceptionOrder,
  fetchReceptionPatient,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  registerWalkIn,
  searchReceptionPatients,
  type DuplicateWarning,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
  type ReceptionPatient,
  type ReceptionTest,
} from "@/lib/api/reception";
import { isRequestAborted, normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

export type SelectedPatient = {
  patientCode: string;
  patientName: string;
};

const SEARCH_DEBOUNCE_MS = 350;

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(value);
}

function asFloat(value: string): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function uniqueIds(items: string[]): string[] {
  return Array.from(new Set(items));
}

export function PatientStep({
  accessToken,
  organizationId,
  initialQuery,
  preservedQuery,
  onSelect,
  onQueryChange,
}: {
  accessToken: string;
  organizationId?: string | null;
  initialQuery?: string;
  preservedQuery?: string;
  onSelect: (patient: SelectedPatient) => void;
  onQueryChange?: (query: string) => void;
}) {
  const [query, setQuery] = useState(preservedQuery ?? initialQuery ?? "");
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(Boolean((preservedQuery ?? initialQuery)?.trim()));
  const [error, setError] = useState<string | null>(null);
  const [create, setCreate] = useState({
    full_name: "",
    phone: "",
    national_id: "",
    gender: "",
    date_of_birth: "",
    email: "",
    address: "",
    patient_code: "",
  });
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<DuplicateWarning[]>([]);
  const searchAbortRef = useRef<AbortController | null>(null);
  const createInFlight = useRef(false);

  async function runSearch(term: string, opts?: { immediate?: boolean }) {
    const q = term.trim();
    searchAbortRef.current?.abort();
    const controller = new AbortController();
    searchAbortRef.current = controller;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        { token: accessToken, organizationId, signal: controller.signal },
        q,
      );
      if (controller.signal.aborted) return;
      setPatients(result.items);
    } catch (err) {
      if (isRequestAborted(err) || controller.signal.aborted) return;
      setPatients([]);
      setError(normalizeApiError(err));
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
    void opts;
  }

  useEffect(() => {
    onQueryChange?.(query);
  }, [query, onQueryChange]);

  useEffect(() => {
    const term = query.trim();
    if (!term) {
      searchAbortRef.current?.abort();
      setLoading(false);
      return;
    }
    const timer = window.setTimeout(() => {
      void runSearch(term);
    }, SEARCH_DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      searchAbortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, accessToken, organizationId]);

  useEffect(() => {
    if (initialQuery?.trim() && !preservedQuery) {
      setQuery(initialQuery);
    }
  }, [initialQuery, preservedQuery]);

  async function submitCreate(force = false) {
    if (createInFlight.current) return;
    if (!create.full_name.trim() || !create.phone.trim()) {
      setCreateError("Full name and phone are required.");
      return;
    }
    createInFlight.current = true;
    setCreating(true);
    setCreateError(null);
    if (!force) setDuplicates([]);
    try {
      if (!force && (create.phone.trim() || create.national_id.trim())) {
        const probe = await searchReceptionPatients(
          { token: accessToken, organizationId },
          create.phone.trim() || create.national_id.trim(),
        );
        const matches = probe.items.filter(
          (p) =>
            (create.phone.trim() && p.phone === create.phone.trim()) ||
            (create.national_id.trim() && p.national_id === create.national_id.trim()),
        );
        if (matches.length > 0) {
          setDuplicates(
            matches.map((p) => ({
              patient_code: p.patient_code,
              full_name: p.full_name,
              phone: p.phone ?? undefined,
              national_id: p.national_id ?? undefined,
              message: `Existing patient ${p.full_name}`,
            })),
          );
          setCreateError("Possible duplicate patient. Review matches or register anyway.");
          return;
        }
      }

      const response = await registerWalkIn(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          full_name: create.full_name.trim(),
          phone: create.phone.trim(),
          national_id: create.national_id.trim() || undefined,
          gender: create.gender.trim() || undefined,
          date_of_birth: create.date_of_birth.trim() || undefined,
          email: create.email.trim() || undefined,
          address: create.address.trim() || undefined,
          patient_code: create.patient_code.trim() || undefined,
          force,
        },
      );

      const confirmed = await fetchReceptionPatient(
        { token: accessToken, organizationId },
        response.patient_code,
      );

      setDuplicates([]);
      onSelect({
        patientCode: confirmed.patient_code,
        patientName: confirmed.full_name,
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
      createInFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="space-y-4">
          <SectionHeader
            title="Patient search"
            description="Search by phone, patient code, national ID, or full name."
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Phone, patient code, national ID, or name"
            aria-label="Patient search"
          />
          <p className="text-xs text-slate-500">Results update as you type (debounced).</p>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={!loading && patients.length === 0}
              emptyLabel="No patients found. Register a new patient on the right."
              onRetry={() => void runSearch(query)}
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
              Type to search an existing patient or register a walk-in.
            </p>
          )}
        </div>

        <Card className="space-y-4">
          <SectionHeader
            title="Create new patient"
            description="Walk-in registration with duplicate detection. Search results stay visible."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
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
              <Label htmlFor="patient_code">Patient code (optional)</Label>
              <Input
                id="patient_code"
                value={create.patient_code}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, patient_code: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="national_id">National ID</Label>
              <Input
                id="national_id"
                value={create.national_id}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, national_id: event.target.value }))
                }
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
            <div>
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
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={create.email}
                onChange={(event) => setCreate((prev) => ({ ...prev, email: event.target.value }))}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="address">Address</Label>
              <Input
                id="address"
                value={create.address}
                onChange={(event) => setCreate((prev) => ({ ...prev, address: event.target.value }))}
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
  onOrderCreated: (
    orderRef: string,
    pricing: ReceptionOrderPricing,
    order: ReceptionOrderCreate["order"],
  ) => void;
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
  const catalogAbortRef = useRef<AbortController | null>(null);
  const createInFlight = useRef(false);

  const categories = useMemo(
    () =>
      Array.from(new Set(tests.map((test) => test.category).filter(Boolean) as string[])).sort(),
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
  const previewSubtotal = useMemo(
    () => selectedTests.reduce((sum, test) => sum + (test.price ?? 0), 0),
    [selectedTests],
  );
  const previewTotal = Math.max(0, previewSubtotal - asFloat(discount));

  async function loadCatalog(q?: string) {
    catalogAbortRef.current?.abort();
    const controller = new AbortController();
    catalogAbortRef.current = controller;
    setLoading(true);
    setError(null);
    try {
      const result = await fetchReceptionTests(
        { token: accessToken, organizationId, signal: controller.signal },
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

  function toggleCategory(category: string) {
    const ids = categoryToTestIds[category] ?? [];
    const isSelected = selectedCategories.includes(category);
    setSelectedCategories((prev) =>
      isSelected ? prev.filter((value) => value !== category) : [...prev, category],
    );
    setSelectedTestIds((prev) =>
      isSelected ? prev.filter((id) => !ids.includes(id)) : uniqueIds([...prev, ...ids]),
    );
  }

  function toggleTest(id: string) {
    setSelectedTestIds((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : uniqueIds([...prev, id]),
    );
  }

  async function submitOrder() {
    if (createInFlight.current) return;
    if (selectedTestIds.length === 0) {
      setError("Select at least one test.");
      return;
    }
    createInFlight.current = true;
    setCreating(true);
    setError(null);
    try {
      const response = await createReceptionOrder(
        { token: accessToken, organizationId, timeoutMs: 30_000 },
        {
          patient_code: patient.patientCode,
          test_catalog_ids: uniqueIds(selectedTestIds),
          discount: asFloat(discount),
          note: note.trim() || undefined,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) throw new Error("Order code not returned by the API.");
      onOrderCreated(orderRef, response.pricing, response.order);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      createInFlight.current = false;
      setCreating(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Select tests & create order"
        description={`${patient.patientName} · ${patient.patientCode}`}
      />
      <Input
        value={catalogQuery}
        onChange={(event) => setCatalogQuery(event.target.value)}
        placeholder="Search test catalog"
        aria-label="Catalog search"
      />
      <DataState
        loading={loading}
        error={error}
        empty={!loading && tests.length === 0}
        emptyLabel="No tests found in master data."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card className="space-y-3">
            <p className="text-sm font-medium text-slate-900">Packages (by category)</p>
            <p className="text-xs text-slate-500">
              Backend has no panel expansion — selecting a package adds its catalog tests.
            </p>
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
                <p className="text-lg font-semibold text-slate-900">
                  {selectedTestIds.length} tests
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600">Preview (not final)</p>
                <p className="font-semibold text-slate-900">{formatCurrency(previewTotal)}</p>
                <p className="text-xs text-slate-500">
                  Authoritative totals come from the API after create.
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
                      onChange={() => toggleTest(row.id)}
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
                { key: "category", label: "Package", render: (row) => row.category ?? "—" },
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
                  <button
                    key={test.id}
                    type="button"
                    className="rounded-full border border-slate-300 bg-white px-3 py-1 text-xs text-slate-700 hover:border-rose-300 hover:text-rose-700"
                    onClick={() => toggleTest(test.id)}
                  >
                    {test.code} ×
                  </button>
                ))}
              </div>
            ) : null}

            <Button
              disabled={creating || selectedTestIds.length === 0}
              onClick={() => void submitOrder()}
            >
              {creating ? "Creating order…" : "Create order"}
            </Button>
          </div>
        </div>
      </DataState>
    </div>
  );
}

export function OrderCreatedStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  order,
  onReset,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onReset: () => void;
}) {
  const [authoritative, setAuthoritative] = useState(pricing);
  const [detail, setDetail] = useState(order);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const items = Array.isArray((detail as { items?: unknown }).items)
    ? ((detail as { items: Record<string, unknown>[] }).items ?? [])
    : [];

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [orderResult, patientResult] = await Promise.all([
        fetchReceptionOrder({ token: accessToken, organizationId }, orderRef),
        fetchReceptionPatient({ token: accessToken, organizationId }, patient.patientCode),
      ]);
      setAuthoritative(orderResult.pricing);
      setDetail(orderResult.order);
      if (!patientResult.patient_code) {
        throw new Error("Patient persistence check failed.");
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderRef, accessToken, organizationId]);

  return (
    <Card className="space-y-4">
      <SectionHeader
        title="Order created"
        description="Milestone 1 complete. Payment and barcode are Milestone 2."
        actions={
          <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>
            {loading ? "Refreshing…" : "Refresh & verify"}
          </Button>
        }
      />
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
          <p className="font-medium text-slate-900">{patient.patientName}</p>
          <p className="text-xs text-slate-500">{patient.patientCode}</p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Authoritative total (API)</p>
          <p className="font-semibold text-slate-900">{formatCurrency(authoritative.total)}</p>
          <p className="text-xs text-slate-500">
            Subtotal {formatCurrency(authoritative.subtotal)} · Discount{" "}
            {formatCurrency(authoritative.discount)}
            {authoritative.tax != null ? ` · Tax ${formatCurrency(authoritative.tax)}` : ""}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <p className="text-xs text-slate-500">Order code</p>
          <p className="break-all font-mono text-sm">{orderRef}</p>
          <p className="text-xs text-slate-500">
            Status: {String((detail as { status?: string }).status ?? "payment_pending")}
          </p>
        </div>
      </div>
      {items.length > 0 ? (
        <SimpleTable
          rows={items}
          rowKey={(row, index) => String(row.id ?? row.test_code ?? index)}
          columns={[
            { key: "code", label: "Code", render: (row) => String(row.test_code ?? "—") },
            { key: "name", label: "Test", render: (row) => String(row.test_name ?? "—") },
            {
              key: "price",
              label: "Unit price",
              render: (row) =>
                row.unit_price != null ? formatCurrency(Number(row.unit_price)) : "—",
            },
          ]}
        />
      ) : null}
      <div className="flex flex-wrap gap-3 border-t border-slate-100 pt-4">
        <Button onClick={onReset}>New order</Button>
        <a href={`/app/reception/workflow?order=${encodeURIComponent(orderRef)}`}>
          <Button variant="outline">Reopen order link</Button>
        </a>
      </div>
    </Card>
  );
}

export { formatCurrency };
