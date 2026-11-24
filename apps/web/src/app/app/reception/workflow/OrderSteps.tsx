"use client";

import { MomoPanel } from "@/components/pilot/MomoPanel";
import { useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  collectReceptionPayment,
  createReceptionOrder,
  fetchReceptionBarcodes,
  fetchReceptionLabHandoff,
  fetchReceptionOrder,
  fetchReceptionPatient,
  fetchReceptionRequestForm,
  fetchReceptionTests,
  getDuplicateWarnings,
  getOrderCode,
  handoffReceptionOrderToLab,
  isValidPatientQr,
  registerWalkIn,
  searchReceptionPatients,
  RECEPTION_LAB_HANDOFF_TIMEOUT_MS,
  RECEPTION_PAYMENT_METHODS,
  RECEPTION_PAYMENT_TIMEOUT_MS,
  type DuplicateWarning,
  type ReceptionBarcodes,
  type ReceptionLabHandoff,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
  type ReceptionPaymentRecord,
  type ReceptionPaymentSummary,
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
        {
          token: accessToken,
          organizationId,
          signal: controller.signal,
          timeoutMs: 30_000,
        },
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
    if (initialQuery?.trim() && !preservedQuery && initialQuery !== query) {
      const timer = window.setTimeout(() => setQuery(initialQuery), 0);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [initialQuery, preservedQuery, query]);

  async function submitCreate(force = false) {
    if (createInFlight.current) return;
    if (!create.full_name.trim() || !create.phone.trim()) {
      setCreateError("Cần nhập họ tên và số điện thoại.");
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
          setCreateError("Có thể trùng bệnh nhân đã có. Hãy xem các kết quả hoặc vẫn đăng ký mới.");
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
        setCreateError("Có thể trùng bệnh nhân đã có. Hãy xem các kết quả bên dưới hoặc vẫn đăng ký mới.");
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
            title="Tìm bệnh nhân"
            description="Tìm theo số điện thoại, mã bệnh nhân, CCCD hoặc họ tên."
          />
          <Input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Số điện thoại, mã bệnh nhân, CCCD hoặc tên"
            aria-label="Tìm bệnh nhân"
          />
          <p className="text-xs text-slate-500">Kết quả cập nhật khi anh/chị gõ.</p>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={!loading && patients.length === 0}
              emptyLabel="Không tìm thấy bệnh nhân. Hãy đăng ký bệnh nhân mới ở bên phải."
              onRetry={() => void runSearch(query)}
            >
              <SimpleTable<ReceptionPatient>
                rows={patients}
                rowKey={(row) => row.patient_code}
                columns={[
                  { key: "code", label: "Mã", render: (row) => row.patient_code },
                  { key: "name", label: "Tên", render: (row) => row.full_name },
                  { key: "phone", label: "Điện thoại", render: (row) => row.phone ?? "—" },
                  { key: "nid", label: "CCCD/CMND", render: (row) => row.national_id ?? "—" },
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
                        Chọn
                      </Button>
                    ),
                  },
                ]}
              />
            </DataState>
          ) : (
            <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Gõ để tìm bệnh nhân đã có hoặc đăng ký bệnh nhân đến trực tiếp.
            </p>
          )}
        </div>

        <Card className="space-y-4">
          <SectionHeader
            title="Tạo bệnh nhân mới"
            description="Đăng ký bệnh nhân đến trực tiếp, có kiểm tra trùng. Kết quả tìm kiếm vẫn hiển thị."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <div className="md:col-span-2">
              <Label htmlFor="full_name">Họ và tên *</Label>
              <Input
                id="full_name"
                value={create.full_name}
                onChange={(event) => setCreate((prev) => ({ ...prev, full_name: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="phone">Số điện thoại *</Label>
              <Input
                id="phone"
                value={create.phone}
                onChange={(event) => setCreate((prev) => ({ ...prev, phone: event.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="patient_code">Mã bệnh nhân (không bắt buộc)</Label>
              <Input
                id="patient_code"
                value={create.patient_code}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, patient_code: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="national_id">CCCD/CMND</Label>
              <Input
                id="national_id"
                value={create.national_id}
                onChange={(event) =>
                  setCreate((prev) => ({ ...prev, national_id: event.target.value }))
                }
              />
            </div>
            <div>
              <Label htmlFor="gender">Giới tính</Label>
              <select
                id="gender"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                value={create.gender}
                onChange={(event) => setCreate((prev) => ({ ...prev, gender: event.target.value }))}
              >
                <option value="">—</option>
                <option value="Nam">Nam</option>
                <option value="Nữ">Nữ</option>
                <option value="Khác">Khác</option>
              </select>
            </div>
            <div>
              <Label htmlFor="dob">Ngày sinh</Label>
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
              <Label htmlFor="address">Địa chỉ</Label>
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
              <p className="text-sm font-medium text-amber-900">Kiểm tra trùng</p>
              <ul className="space-y-2 text-sm text-amber-900">
                {duplicates.map((warning, index) => (
                  <li
                    key={`${warning.patient_code ?? warning.field ?? "dup"}-${index}`}
                    className="flex flex-wrap items-center justify-between gap-2"
                  >
                    <span>
                      {String(warning.message ?? warning.reason ?? "Có thể trùng")}
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
                        Dùng bệnh nhân này
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
                {creating ? "Đang đăng ký…" : "Vẫn đăng ký mới"}
              </Button>
            </div>
          ) : null}
          <Button onClick={() => void submitCreate(false)} disabled={creating}>
            {creating ? "Đang đăng ký…" : "Đăng ký và tiếp tục"}
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
  const [collectionMode, setCollectionMode] = useState<
    "AT_RECEPTION" | "HOME_COLLECTION" | "CLINIC_COLLECTION"
  >("AT_RECEPTION");
  const [pickupAddress, setPickupAddress] = useState("");
  const [pickupProvince, setPickupProvince] = useState("");
  const [pickupDistrict, setPickupDistrict] = useState("");
  const [pickupWard, setPickupWard] = useState("");
  const [contactPerson, setContactPerson] = useState(patient.patientName);
  const [contactPhone, setContactPhone] = useState("");
  const [requestedDate, setRequestedDate] = useState("");
  const [timeWindow, setTimeWindow] = useState("");
  const [clinicName, setClinicName] = useState("");
  const [specimenType, setSpecimenType] = useState("BLOOD");
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
      setError("Hãy chọn ít nhất một xét nghiệm.");
      return;
    }
    if (collectionMode === "HOME_COLLECTION") {
      if (
        !pickupAddress.trim() ||
        !pickupProvince.trim() ||
        !pickupDistrict.trim() ||
        !contactPerson.trim() ||
        !contactPhone.trim() ||
        !requestedDate ||
        !timeWindow.trim()
      ) {
        setError("Thu mẫu tại nhà cần địa chỉ, tỉnh/thành, quận/huyện, người liên hệ, số điện thoại, ngày và khung giờ.");
        return;
      }
    }
    if (collectionMode === "CLINIC_COLLECTION") {
      if (!clinicName.trim() || !requestedDate || !timeWindow.trim()) {
        setError("Thu mẫu tại phòng khám cần phòng khám, ngày và giờ mong muốn.");
        return;
      }
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
          collection_mode: collectionMode,
          specimen_type: specimenType.trim() || "BLOOD",
          pickup_address: collectionMode === "HOME_COLLECTION" ? pickupAddress.trim() : undefined,
          pickup_province: collectionMode === "HOME_COLLECTION" ? pickupProvince.trim() : undefined,
          pickup_district: collectionMode === "HOME_COLLECTION" ? pickupDistrict.trim() : undefined,
          pickup_ward: collectionMode === "HOME_COLLECTION" ? pickupWard.trim() || undefined : undefined,
          contact_person:
            collectionMode === "HOME_COLLECTION" ? contactPerson.trim() : undefined,
          contact_phone: collectionMode === "HOME_COLLECTION" ? contactPhone.trim() : undefined,
          requested_date: collectionMode === "AT_RECEPTION" ? undefined : requestedDate,
          requested_time_window: collectionMode === "AT_RECEPTION" ? undefined : timeWindow.trim(),
          clinic_name: collectionMode === "CLINIC_COLLECTION" ? clinicName.trim() : undefined,
        },
      );
      const orderRef = getOrderCode(response.order);
      if (!orderRef) throw new Error("Hệ thống không trả về mã đơn.");
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
        title="Chọn xét nghiệm và tạo đơn"
        description={`${patient.patientName} · ${patient.patientCode}`}
      />
      <Input
        value={catalogQuery}
        onChange={(event) => setCatalogQuery(event.target.value)}
        placeholder="Tìm danh mục xét nghiệm"
        aria-label="Tìm danh mục"
      />
      {/* empty=false: catalog miss must not hide collection method / create order controls */}
      <DataState
        loading={loading}
        error={error}
        empty={false}
        emptyLabel="Không tìm thấy xét nghiệm trong danh mục."
        onRetry={() => void loadCatalog(catalogQuery)}
      >
        <div className="grid gap-4 lg:grid-cols-[260px_1fr]">
          <Card className="space-y-3">
            <p className="text-sm font-medium text-slate-900">Gói xét nghiệm (theo nhóm)</p>
            <p className="text-xs text-slate-500">
              Chọn một gói sẽ thêm các xét nghiệm của gói đó vào đơn.
            </p>
            {categories.length === 0 ? (
              <p className="text-sm text-slate-500">Chưa có gói xét nghiệm nào.</p>
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
                <p className="text-sm text-slate-600">Đã chọn</p>
                <p className="text-lg font-semibold text-slate-900">
                  {selectedTestIds.length} xét nghiệm
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-slate-600">Xem trước (chưa chính thức)</p>
                <p className="font-semibold text-slate-900">{formatCurrency(previewTotal)}</p>
                <p className="text-xs text-slate-500">
                  Tổng tiền chính thức do hệ thống tính sau khi tạo đơn.
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <Label htmlFor="discount">Giảm giá</Label>
                <Input
                  id="discount"
                  value={discount}
                  onChange={(event) => setDiscount(event.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="note">Ghi chú</Label>
                <Input id="note" value={note} onChange={(event) => setNote(event.target.value)} />
              </div>
            </div>

            <div className="space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-900">Cách thu mẫu</p>
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={collectionMode}
                onChange={(e) =>
                  setCollectionMode(
                    e.target.value as "AT_RECEPTION" | "HOME_COLLECTION" | "CLINIC_COLLECTION",
                  )
                }
                aria-label="Cách thu mẫu"
              >
                <option value="AT_RECEPTION">Tại quầy tiếp nhận</option>
                <option value="HOME_COLLECTION">Tại nhà</option>
                <option value="CLINIC_COLLECTION">Tại phòng khám</option>
              </select>
              <div>
                <Label htmlFor="laboratory-legacy">Phòng xét nghiệm</Label>
                <select
                  id="laboratory-legacy"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  defaultValue="central"
                  aria-label="Phòng xét nghiệm"
                >
                  <option value="central">Phòng xét nghiệm trung tâm DxCon</option>
                </select>
              </div>
              <div>
                <Label htmlFor="specimen-type-legacy">Loại mẫu</Label>
                <Input
                  id="specimen-type-legacy"
                  value={specimenType}
                  onChange={(e) => setSpecimenType(e.target.value)}
                />
              </div>
              {collectionMode === "HOME_COLLECTION" ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <Label htmlFor="pickup-address">Địa chỉ lấy mẫu *</Label>
                    <Input id="pickup-address" value={pickupAddress} onChange={(e) => setPickupAddress(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="pickup-province">Tỉnh/Thành *</Label>
                    <Input id="pickup-province" value={pickupProvince} onChange={(e) => setPickupProvince(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="pickup-district">Quận/Huyện *</Label>
                    <Input id="pickup-district" value={pickupDistrict} onChange={(e) => setPickupDistrict(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="pickup-ward">Phường/Xã</Label>
                    <Input id="pickup-ward" value={pickupWard} onChange={(e) => setPickupWard(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="contact-person">Người liên hệ *</Label>
                    <Input id="contact-person" value={contactPerson} onChange={(e) => setContactPerson(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="contact-phone">Số điện thoại *</Label>
                    <Input id="contact-phone" value={contactPhone} onChange={(e) => setContactPhone(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="req-date">Ngày mong muốn *</Label>
                    <Input id="req-date" type="date" value={requestedDate} onChange={(e) => setRequestedDate(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="time-window">Khung giờ mong muốn *</Label>
                    <Input id="time-window" value={timeWindow} onChange={(e) => setTimeWindow(e.target.value)} />
                  </div>
                </div>
              ) : null}
              {collectionMode === "CLINIC_COLLECTION" ? (
                <div className="grid gap-3 md:grid-cols-2">
                  <div className="md:col-span-2">
                    <Label htmlFor="clinic-name">Phòng khám *</Label>
                    <Input id="clinic-name" value={clinicName} onChange={(e) => setClinicName(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="clinic-date">Ngày mong muốn *</Label>
                    <Input id="clinic-date" type="date" value={requestedDate} onChange={(e) => setRequestedDate(e.target.value)} />
                  </div>
                  <div>
                    <Label htmlFor="clinic-time">Giờ mong muốn *</Label>
                    <Input id="clinic-time" value={timeWindow} onChange={(e) => setTimeWindow(e.target.value)} />
                  </div>
                </div>
              ) : null}
            </div>

            {!loading && !error && tests.length === 0 ? (
              <p className="rounded-xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-500">
                Không tìm thấy xét nghiệm trong danh mục. Phần chọn cách thu mẫu bên dưới vẫn dùng được; hãy thử tìm lại ở trên.
              </p>
            ) : null}
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
                { key: "code", label: "Mã", render: (row) => row.code },
                { key: "name", label: "Xét nghiệm", render: (row) => row.name },
                {
                  key: "specimen",
                  label: "Mẫu",
                  render: (row) => row.sample_type ?? "—",
                },
                {
                  key: "tat",
                  label: "TAT (giờ)",
                  render: (row) =>
                    row.turnaround_hours != null ? String(row.turnaround_hours) : "—",
                },
                { key: "category", label: "Gói", render: (row) => row.category ?? "—" },
                {
                  key: "price",
                  label: "Giá niêm yết",
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
              {creating ? "Đang tạo đơn…" : "Tạo đơn"}
            </Button>
          </div>
        </div>
      </DataState>
    </div>
  );
}


export function OrderCreatedStep(props: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onReset: () => void;
  cashierLabel?: string | null;
}) {
  return <PaymentStep {...props} />;
}

/**
 * Open generated HTML (receipt, labels, requisition) in a new window and print it.
 * A blob URL is used because window.open("", "_blank", "noopener") returns null,
 * which left a blank page: the document was never written into it.
 */
function openHtmlWindow(html: string, features?: string): void {
  const url = URL.createObjectURL(new Blob([html], { type: "text/html" }));
  window.open(url, "_blank", features ? `noopener,noreferrer,${features}` : "noopener,noreferrer");
  window.setTimeout(() => URL.revokeObjectURL(url), 120_000);
}

export function PaymentStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  order,
  onReset,
  cashierLabel,
  onPaymentRecorded,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  order: ReceptionOrderCreate["order"];
  onReset: () => void;
  cashierLabel?: string | null;
  onPaymentRecorded?: () => void;
}) {
  const [authoritative, setAuthoritative] = useState(pricing);
  const [detail, setDetail] = useState(order);
  const [summary, setSummary] = useState<ReceptionPaymentSummary>(() => ({
    order_total: pricing.total,
    paid_amount: 0,
    outstanding_amount: pricing.total,
    discount: pricing.discount,
    subtotal: pricing.subtotal,
    tax: pricing.tax ?? null,
    status: "unpaid",
    payment_methods_supported: [...RECEPTION_PAYMENT_METHODS],
    partial_payments_supported: true,
  }));
  const [payment, setPayment] = useState<ReceptionPaymentRecord | null>(null);
  const [loading, setLoading] = useState(false);
  const [paying, setPaying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState("cash");
  const [amountInput, setAmountInput] = useState(String(pricing.total));
  const [showDocuments, setShowDocuments] = useState(false);
  const [idempotencyKey, setIdempotencyKey] = useState(() =>
    typeof crypto !== "undefined" && crypto.randomUUID
      ? `pay-${crypto.randomUUID()}`
      : `pay-${Date.now()}`,
  );
  const submitLock = useRef(false);

  const items = Array.isArray((detail as { items?: unknown }).items)
    ? ((detail as { items: Record<string, unknown>[] }).items ?? [])
    : [];
  const methods =
    summary.payment_methods_supported?.length
      ? summary.payment_methods_supported
      : [...RECEPTION_PAYMENT_METHODS];
  const isPaid = summary.status === "paid" || summary.outstanding_amount <= 0;

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const orderResult = await fetchReceptionOrder(
        { token: accessToken, organizationId },
        orderRef,
        { patientCode: patient.patientCode },
      );
      setAuthoritative(orderResult.pricing);
      setDetail(orderResult.order);
      if (orderResult.payment_summary) {
        setSummary(orderResult.payment_summary);
        setAmountInput(String(orderResult.payment_summary.outstanding_amount));
      }
      if (orderResult.payment) setPayment(orderResult.payment);
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

  function validateAmount(raw: string, outstanding: number, allowPartial: boolean): number {
    const value = Number(raw);
    if (!Number.isFinite(value)) throw new Error("Hãy nhập số tiền thanh toán hợp lệ.");
    if (value <= 0) throw new Error("Số tiền thanh toán phải lớn hơn 0.");
    if (value > outstanding + 0.0001) {
      throw new Error(`Không được trả vượt quá. Số còn phải trả là ${formatCurrency(outstanding)}.`);
    }
    if (!allowPartial && value + 0.0001 < outstanding) {
      throw new Error(
        "Chưa hỗ trợ thanh toán một phần. Số tiền phải bằng số còn phải trả.",
      );
    }
    return value;
  }

  async function submitPayment() {
    if (submitLock.current || paying) return;
    setError(null);
    let amount: number;
    try {
      amount = validateAmount(
        amountInput,
        summary.outstanding_amount,
        Boolean(summary.partial_payments_supported),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Số tiền không hợp lệ");
      return;
    }
    submitLock.current = true;
    setPaying(true);
    try {
      const result = await collectReceptionPayment(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_PAYMENT_TIMEOUT_MS },
        orderRef,
        { payment_method: paymentMethod, amount, idempotency_key: idempotencyKey },
      );
      setSummary(result.payment_summary);
      setPayment(result.payment);
      if (result.payment_summary.status !== "paid") {
        setIdempotencyKey(
          typeof crypto !== "undefined" && crypto.randomUUID
            ? `pay-${crypto.randomUUID()}`
            : `pay-${Date.now()}`,
        );
        setAmountInput(String(result.payment_summary.outstanding_amount));
      }
      await refresh();
      onPaymentRecorded?.();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setPaying(false);
      submitLock.current = false;
    }
  }

  function openPrintableReceipt() {
    if (!payment) return;
    const paidAt = payment.paid_at ? new Date(payment.paid_at).toLocaleString() : "—";
    const cashier = cashierLabel || payment.created_by || "—";
    const html = `<!doctype html><html><head><title>Receipt ${escapeHtml(payment.receipt_number)}</title>
<style>body{font-family:ui-monospace,Menlo,monospace;padding:24px}.row{display:flex;justify-content:space-between;margin:6px 0;font-size:13px}.hr{border-top:1px dashed #94a3b8;margin:12px 0}</style></head><body>
<h1>Biên lai tiếp nhận DxCon</h1>
<div class="row"><span>Biên lai</span><span>${escapeHtml(payment.receipt_number)}</span></div>
<div class="row"><span>Đơn</span><span>${escapeHtml(orderRef)}</span></div>
<div class="row"><span>Bệnh nhân</span><span>${escapeHtml(patient.patientName)} (${escapeHtml(patient.patientCode)})</span></div>
<div class="hr"></div>
<div class="row"><span>Hình thức</span><span>${escapeHtml(payment.payment_method)}</span></div>
<div class="row"><span>Số tiền</span><span>${escapeHtml(formatCurrency(payment.amount))}</span></div>
<div class="row"><span>Trạng thái</span><span>${escapeHtml(summary.status)}</span></div>
<div class="row"><span>Thanh toán lúc</span><span>${escapeHtml(paidAt)}</span></div>
<div class="row"><span>Thu ngân</span><span>${escapeHtml(cashier)}</span></div>
<script>window.onload=function(){window.print()}</script></body></html>`;
    openHtmlWindow(html, "width=480,height=720");
  }

  if (showDocuments && isPaid) {
    return (
      <DocumentsStep
        accessToken={accessToken}
        organizationId={organizationId}
        patient={patient}
        orderRef={orderRef}
        pricing={authoritative}
        payment={payment}
        cashierLabel={cashierLabel}
        onReset={onReset}
        onBackToPayment={() => setShowDocuments(false)}
      />
    );
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <SectionHeader
          title="Thanh toán và biên lai"
          description="Thu tiền theo tổng tiền chính thức. Chứng từ được mở sau khi đã thanh toán."
          actions={
            <Button size="sm" variant="outline" disabled={loading} onClick={() => void refresh()}>
              {loading ? "Đang làm mới…" : "Làm mới"}
            </Button>
          }
        />
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void refresh()}>
              Thử lại
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Bệnh nhân</p>
            <p className="font-medium text-slate-900">{patient.patientName}</p>
            <p className="text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Tổng tiền đơn</p>
            <p className="font-semibold text-slate-900">{formatCurrency(summary.order_total)}</p>
            <p className="text-xs text-slate-500">
              Subtotal {formatCurrency(summary.subtotal ?? authoritative.subtotal)} · Discount{" "}
              {formatCurrency(summary.discount ?? authoritative.discount)}
            </p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Đã trả / còn phải trả</p>
            <p className="font-semibold text-slate-900">{formatCurrency(summary.paid_amount)}</p>
            <p className="text-xs text-slate-500">Due {formatCurrency(summary.outstanding_amount)}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Đơn · trạng thái</p>
            <p className="break-all font-mono text-sm">{orderRef}</p>
            <p className="text-xs font-medium uppercase text-slate-600">{summary.status}</p>
          </div>
        </div>
        {items.length > 0 ? (
          <SimpleTable
            rows={items}
            rowKey={(row, index) => String(row.id ?? row.test_code ?? index)}
            columns={[
              { key: "code", label: "Mã", render: (row) => String(row.test_code ?? "—") },
              { key: "name", label: "Xét nghiệm", render: (row) => String(row.test_name ?? "—") },
              {
                key: "price",
                label: "Đơn giá",
                render: (row) =>
                  row.unit_price != null ? formatCurrency(Number(row.unit_price)) : "—",
              },
            ]}
          />
        ) : null}
      </Card>

      {!isPaid ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Thanh toán số còn lại"
            description="Chỉ thanh toán đủ một lần. Số tiền phải bằng số còn phải trả."
          />
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label htmlFor="payment_method">Hình thức thanh toán</Label>
              <select
                id="payment_method"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
                value={paymentMethod}
                onChange={(event) => setPaymentMethod(event.target.value)}
                disabled={paying}
              >
                {methods.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <Label htmlFor="pay_amount">Số tiền phải trả</Label>
              <Input
                id="pay_amount"
                inputMode="decimal"
                value={amountInput}
                onChange={(event) => setAmountInput(event.target.value)}
                disabled={paying}
              />
            </div>
          </div>
          <Button disabled={paying || loading} onClick={() => void submitPayment()}>
            {paying ? "Đang ghi nhận thanh toán…" : "Thu tiền"}
          </Button>
          <MomoPanel
            orderRef={orderRef}
            ctx={{ token: accessToken, organizationId }}
            onPaid={() => {
              void refresh();
              onPaymentRecorded?.();
            }}
          />
        </Card>
      ) : (
        <Card className="space-y-4">
          <SectionHeader title="Biên lai" description="Thanh toán đã được hệ thống ghi nhận." />
          {payment ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Biên lai / mã tham chiếu</p>
                <p className="font-mono text-sm">{payment.receipt_number}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Ngày / giờ</p>
                <p className="text-sm">
                  {payment.paid_at ? new Date(payment.paid_at).toLocaleString() : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Hình thức</p>
                <p className="text-sm">{payment.payment_method}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Số tiền</p>
                <p className="text-sm font-semibold">{formatCurrency(payment.amount)}</p>
              </div>
              <div className="rounded-lg border border-slate-200 p-3">
                <p className="text-xs text-slate-500">Thu ngân</p>
                <p className="text-sm">{cashierLabel || payment.created_by || "—"}</p>
              </div>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" disabled={!payment} onClick={openPrintableReceipt}>
              In biên lai
            </Button>
            <Button onClick={() => setShowDocuments(true)}>Tiếp tục: mã vạch và phiếu chỉ định</Button>
            <Button variant="ghost" onClick={onReset}>
              Đơn mới
            </Button>
          </div>
        </Card>
      )}
    </div>
  );
}

export function DocumentsStep({
  accessToken,
  organizationId,
  patient,
  orderRef,
  pricing,
  payment,
  cashierLabel,
  onReset,
  onBackToPayment,
}: {
  accessToken: string;
  organizationId?: string | null;
  patient: SelectedPatient;
  orderRef: string;
  pricing: ReceptionOrderPricing;
  payment: ReceptionPaymentRecord | null;
  cashierLabel?: string | null;
  onReset: () => void;
  onBackToPayment?: () => void;
}) {
  const [barcodes, setBarcodes] = useState<ReceptionBarcodes | null>(null);
  const [requisitionHtml, setRequisitionHtml] = useState<string | null>(null);
  const [handoff, setHandoff] = useState<ReceptionLabHandoff | null>(null);
  const [loading, setLoading] = useState(false);
  const [handingOff, setHandingOff] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [handoffError, setHandoffError] = useState<string | null>(null);
  const handoffLock = useRef(false);

  const documentsReady = Boolean(
    barcodes?.order_barcode &&
      (barcodes.sample_barcodes?.length ?? 0) > 0 &&
      (requisitionHtml || "").trim(),
  );
  const alreadyHandedOff = Boolean(
    handoff?.handed_off ||
      handoff?.order_status === "lab_received" ||
      handoff?.order_status === "testing",
  );

  async function loadDocuments() {
    setLoading(true);
    setError(null);
    try {
      const [codes, form, status] = await Promise.all([
        fetchReceptionBarcodes({ token: accessToken, organizationId }, orderRef),
        fetchReceptionRequestForm({ token: accessToken, organizationId }, orderRef),
        fetchReceptionLabHandoff(
          { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
          orderRef,
        ).catch(() => null),
      ]);
      if (!isValidPatientQr(codes.patient_qr)) {
        throw new Error("Mã QR bệnh nhân từ hệ thống không hợp lệ.");
      }
      setBarcodes(codes);
      setRequisitionHtml(form.html);
      if (status?.handed_off) {
        setHandoff(status);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadDocuments();
    }, 0);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orderRef, accessToken, organizationId]);

  async function submitHandoff() {
    if (handoffLock.current || handingOff || alreadyHandedOff || !documentsReady) return;
    handoffLock.current = true;
    setHandingOff(true);
    setHandoffError(null);
    try {
      const result = await handoffReceptionOrderToLab(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
        orderRef,
      );
      setHandoff(result);
      const refreshed = await fetchReceptionLabHandoff(
        { token: accessToken, organizationId, timeoutMs: RECEPTION_LAB_HANDOFF_TIMEOUT_MS },
        orderRef,
      );
      setHandoff(refreshed);
    } catch (err) {
      setHandoffError(normalizeApiError(err));
    } finally {
      setHandingOff(false);
      handoffLock.current = false;
    }
  }

  function openLabels() {
    if (!barcodes) return;
    const sampleRows = (barcodes.sample_barcodes || [])
      .map(
        (s) => `<div class="label"><div><strong>${escapeHtml(s.barcode)}</strong></div>
<div>${escapeHtml(patient.patientName)} · ${escapeHtml(patient.patientCode)}</div>
<div>${escapeHtml(orderRef)} · ${escapeHtml(s.test_code)}</div>
<div>${escapeHtml(s.sample_type || s.test_name)}</div>
<div>${escapeHtml(s.collection_requirement || "Thu mẫu thông thường")}</div>
<div>${escapeHtml(barcodes.generated_at || "")}</div></div>`,
      )
      .join("");
    const html = `<!doctype html><html><head><title>Labels ${escapeHtml(orderRef)}</title>
<style>
body{font-family:ui-monospace,Menlo,monospace;padding:16px}
.label{border:1px solid #0f172a;padding:12px;margin:0 0 12px;width:320px;page-break-inside:avoid;font-size:12px}
</style></head><body>
<div class="label"><div><strong>${escapeHtml(barcodes.order_barcode)}</strong></div>
<div>Order ${escapeHtml(orderRef)}</div>
<div>${escapeHtml(patient.patientName)} (${escapeHtml(patient.patientCode)})</div>
<div>QR ${escapeHtml(barcodes.patient_qr)}</div>
<div>${escapeHtml(barcodes.generated_at || "")}</div></div>
${sampleRows}
<script>window.onload=function(){window.print()}</script></body></html>`;
    openHtmlWindow(html, "width=420,height=720");
  }

  function openRequisition() {
    if (!requisitionHtml) return;
    openHtmlWindow(requisitionHtml);
  }

  return (
    <div className="space-y-5">
      <Card className="space-y-4">
        <SectionHeader
          title="Mã vạch, QR và phiếu chỉ định"
          description="Mã định danh do hệ thống tạo cho đơn đã thanh toán. In lại sẽ ra đúng các mã cũ."
          actions={
            <Button size="sm" variant="outline" disabled={loading} onClick={() => void loadDocuments()}>
              {loading ? "Đang tải…" : barcodes?.reprint ? "In lại / làm mới" : "Tạo / làm mới"}
            </Button>
          }
        />
        {error ? (
          <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <p>{error}</p>
            <Button className="mt-2" size="sm" variant="outline" onClick={() => void loadDocuments()}>
              Thử lại
            </Button>
          </div>
        ) : null}
        <div className="grid gap-3 md:grid-cols-3">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Đơn</p>
            <p className="font-mono text-sm">{orderRef}</p>
            <p className="text-xs text-slate-500">Tổng {formatCurrency(pricing.total)}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Bệnh nhân</p>
            <p className="font-medium">{patient.patientName}</p>
            <p className="text-xs text-slate-500">{patient.patientCode}</p>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
            <p className="text-xs text-slate-500">Biên lai</p>
            <p className="font-mono text-sm">{payment?.receipt_number ?? "—"}</p>
            <p className="text-xs text-slate-500">{cashierLabel || payment?.created_by || "—"}</p>
          </div>
        </div>
      </Card>

      {barcodes ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Mã định danh"
            description={
              barcodes.reprint
                ? "In lại — giữ nguyên các mã đã tạo (không tạo mã mới)."
                : "Lần tạo đầu tiên — mã định danh đã được lưu cho đơn này."
            }
          />
          <div className="grid gap-3 md:grid-cols-2">
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Mã vạch đơn</p>
              <p className="font-mono text-sm">{barcodes.order_barcode}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Mã vạch bệnh nhân</p>
              <p className="font-mono text-sm">{barcodes.patient_barcode}</p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3 md:col-span-2">
              <p className="text-xs text-slate-500">Nội dung QR bệnh nhân</p>
              <p className="break-all font-mono text-sm">{barcodes.patient_qr}</p>
              <p className="mt-1 text-xs text-emerald-700">
                {isValidPatientQr(barcodes.patient_qr) ? "Định dạng QR hợp lệ" : "Định dạng QR không hợp lệ"}
              </p>
            </div>
            <div className="rounded-lg border border-slate-200 p-3">
              <p className="text-xs text-slate-500">Tạo lúc</p>
              <p className="text-sm">
                {barcodes.generated_at
                  ? new Date(barcodes.generated_at).toLocaleString()
                  : "—"}
              </p>
            </div>
          </div>
          {barcodes.sample_barcodes?.length ? (
            <SimpleTable
              rows={barcodes.sample_barcodes}
              rowKey={(row, index) => `${row.barcode}-${index}`}
              columns={[
                { key: "specimen", label: "Mẫu", render: (row) => row.specimen_code ?? "—" },
                { key: "barcode", label: "Mã vạch", render: (row) => row.barcode },
                { key: "test", label: "Xét nghiệm", render: (row) => `${row.test_code} · ${row.test_name}` },
                { key: "type", label: "Loại", render: (row) => row.sample_type ?? "—" },
              ]}
            />
          ) : null}
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={openLabels}>
              In nhãn
            </Button>
            <Button variant="outline" disabled={!requisitionHtml} onClick={openRequisition}>
              Mở phiếu chỉ định
            </Button>
            <Button variant="ghost" onClick={() => void loadDocuments()}>
              In lại
            </Button>
          </div>
        </Card>
      ) : loading ? (
        <p className="text-sm text-slate-500">Đang tạo mã định danh…</p>
      ) : null}

      {documentsReady ? (
        <Card className="space-y-4">
          <SectionHeader
            title="Bàn giao cho phòng xét nghiệm"
            description="Chuyển đơn đã thanh toán và đủ chứng từ này vào hàng đợi của phòng xét nghiệm (một lần)."
          />
          {handoffError ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
              <p>{handoffError}</p>
              <Button
                className="mt-2"
                size="sm"
                variant="outline"
                disabled={handingOff || alreadyHandedOff}
                onClick={() => void submitHandoff()}
              >
                Thử bàn giao lại
              </Button>
            </div>
          ) : null}
          {alreadyHandedOff ? (
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Tiếp nhận lúc</p>
                <p className="text-sm text-emerald-900">
                  {handoff?.accepted_at ? new Date(handoff.accepted_at).toLocaleString() : "—"}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Trạng thái đơn / mẫu</p>
                <p className="text-sm font-medium uppercase text-emerald-900">
                  {handoff?.order_status ?? "—"}
                  {handoff?.collection?.status
                    ? ` · ${String(handoff.collection.status)}`
                    : ""}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Phòng xét nghiệm nhận</p>
                <p className="text-sm text-emerald-900">
                  {handoff?.laboratory.name ?? "Phòng xét nghiệm trung tâm"}
                </p>
              </div>
              <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3">
                <p className="text-xs text-emerald-700">Mã hàng đợi</p>
                <p className="font-mono text-sm text-emerald-900">
                  {handoff?.queue_reference ?? "—"}
                </p>
              </div>
            </div>
          ) : (
            <Button
              disabled={handingOff || !documentsReady}
              onClick={() => void submitHandoff()}
            >
              {handingOff ? "Đang bàn giao…" : "Bàn giao cho phòng xét nghiệm"}
            </Button>
          )}
          {alreadyHandedOff ? (
            <p className="text-xs text-slate-500">
              Đã bàn giao xong. Không thể bàn giao lại; bấm làm mới để tải lại trạng thái.
            </p>
          ) : null}
        </Card>
      ) : null}

      <div className="flex flex-wrap gap-3">
        {onBackToPayment ? (
          <Button variant="outline" onClick={onBackToPayment}>
            Quay lại biên lai
          </Button>
        ) : null}
        <Button onClick={onReset}>Đơn mới</Button>
        <a href={`/app/reception/workflow?order=${encodeURIComponent(orderRef)}`}>
          <Button variant="ghost">Mở lại liên kết đơn</Button>
        </a>
      </div>
    </div>
  );
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export { formatCurrency };
