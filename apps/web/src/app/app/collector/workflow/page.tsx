"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { JobInfoCard } from "@/components/pilot/JobInfoCard";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import {
  QUALITY_REJECTION_OPTIONS,
  arriveAtLab,
  collectSpecimen,
  dispatchCollection,
  fetchCollection,
  fetchCollectionQueue,
  handoffCollection,
  rejectSpecimen,
  type SampleCollectionItem,
  verifyCollection,
} from "@/lib/api/sampleCollection";
import { normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, StatusPill } from "../_components/ui";

const STEPS = ["Xác minh", "Lấy mẫu", "Vận chuyển", "Đến phòng XN"] as const;

const REJECT_VI: Record<string, string> = {
  insufficient_volume: "Không đủ thể tích mẫu",
  wrong_tube: "Sai loại ống",
  hemolyzed: "Mẫu bị vỡ hồng cầu (tán huyết)",
  contaminated: "Mẫu bị nhiễm bẩn",
  mismatched_identifier: "Sai/lệch mã định danh",
  rejected: "Từ chối (lý do khác)",
};

function CollectorWorkflowPanel() {
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const searchParams = useSearchParams();
  const idParam = searchParams.get("id");

  const [step, setStep] = useState(0);
  const [queue, setQueue] = useState<SampleCollectionItem[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(idParam);
  const [detail, setDetail] = useState<SampleCollectionItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [specimenId, setSpecimenId] = useState<string | null>(null);

  const [patientName, setPatientName] = useState("");
  const [bookingCode, setBookingCode] = useState("");
  const [scannedBarcode, setScannedBarcode] = useState("");
  const [specimenType, setSpecimenType] = useState("BLOOD");
  const [location, setLocation] = useState("");
  const [notes, setNotes] = useState("");
  const [qualityStatus, setQualityStatus] = useState("insufficient_volume");
  const [rejectReason, setRejectReason] = useState("");
  const [temperature, setTemperature] = useState("");
  const [eta, setEta] = useState("");
  const [distance, setDistance] = useState("");

  const canWrite =
    can("collections.write") ||
    ["COLLECTOR", "PARTNER_COLLECTOR", "DRIVER", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(
      role ?? "",
    );

  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );

  const refreshDetail = useCallback(
    async (collectionId: string) => {
      const row = await fetchCollection(auth, collectionId);
      setDetail(row);
      setPatientName(row.booking?.patient_name || "");
      setBookingCode(row.booking?.booking_code || "");
      setScannedBarcode(row.expected_barcode || row.barcode_value || "");
      setSpecimenType(row.specimen_type || "BLOOD");
      setLocation(row.collection_location || row.booking?.patient_address || "");
      if (row.sample_tracking?.sample_code) {
        setSpecimenId(row.sample_tracking.sample_code);
      }
      const status = String(row.status || "").toUpperCase();
      if (status === "RECEIVED" || status === "ARRIVED_AT_LAB") setStep(3);
      else if (status === "IN_TRANSIT" || status === "COLLECTED") setStep(2);
      else if (
        status === "VERIFIED" ||
        status === "CHECKED_IN" ||
        (row.patient_verified && row.order_verified)
      )
        setStep(1);
      else setStep(0);
      return row;
    },
    [auth],
  );

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCollectionQueue(auth, { include_desk: false });
      const items = (data.items ?? []).filter(
        (item) =>
          item.collection_mode !== "AT_RECEPTION" &&
          item.source !== "desk" &&
          item.source !== "reception",
      );
      setQueue(items);
      const target = selectedId || idParam || items[0]?.id || null;
      setSelectedId(target);
      if (target) {
        await refreshDetail(target);
      } else {
        setDetail(null);
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth, idParam, refreshDetail, selectedId]);

  useEffect(() => {
    void load();
    // initial load only when token / idParam changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken, idParam]);

  async function onSelect(id: string) {
    setSelectedId(id);
    setMessage(null);
    setError(null);
    setBusy(true);
    try {
      await refreshDetail(id);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onVerify() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await verifyCollection(auth, selectedId, {
        patient_name: patientName || undefined,
        booking_code: bookingCode || undefined,
        scanned_barcode: scannedBarcode || undefined,
      });
      setMessage("Đã xác minh bệnh nhân và đơn.");
      setStep(1);
      await refreshDetail(selectedId);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onCollect() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await collectSpecimen(auth, selectedId, {
        scanned_barcode: scannedBarcode,
        specimen_type: specimenType,
        collection_location: location || undefined,
        notes: notes || undefined,
        require_barcode: true,
        patient_verified: true,
        order_verified: true,
        collector_id: detail?.collector_id || undefined,
      });
      const code = String(result.sample_tracking?.sample_code ?? "");
      if (code) setSpecimenId(code);
      setMessage(`Đã lấy mẫu${code ? `: ${code}` : ""}.`);
      setStep(2);
      await refreshDetail(selectedId);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onReject() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = await rejectSpecimen(auth, selectedId, {
        quality_status: qualityStatus,
        rejection_reason: rejectReason || undefined,
        request_recollect: true,
      });
      setMessage(
        result.recollect
          ? `Rejected. Recollect queued: ${result.recollect.id.slice(0, 8)}…`
          : "Đã từ chối mẫu.",
      );
      if (result.recollect?.id) {
        setSelectedId(result.recollect.id);
        await refreshDetail(result.recollect.id);
        setStep(0);
      } else {
        await load();
      }
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onDispatch() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      if (detail?.marketplace_booking_id) {
        await dispatchCollection(
          auth,
          detail.marketplace_booking_id,
          {
            temperature_c: temperature ? Number(temperature) : undefined,
            eta_minutes: eta ? Number(eta) : undefined,
            distance_km: distance ? Number(distance) : undefined,
            driver_id: detail.collector_id || undefined,
          },
          { by: "booking" },
        );
      } else {
        await dispatchCollection(auth, selectedId, {
          temperature_c: temperature ? Number(temperature) : undefined,
          eta_minutes: eta ? Number(eta) : undefined,
          distance_km: distance ? Number(distance) : undefined,
          driver_id: detail?.collector_id || undefined,
        });
      }
      await handoffCollection(auth, selectedId, {
        temperature_c: temperature ? Number(temperature) : undefined,
        note: "Đã ghi nhận bàn giao của nhân viên thu mẫu",
      });
      await refreshDetail(selectedId);
      setMessage("Đã ghi nhận bàn giao và xuất phát.");
      setStep(3);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  async function onLabArrive() {
    if (!selectedId || !canWrite) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const result = detail?.marketplace_booking_id
        ? await arriveAtLab(
            auth,
            detail.marketplace_booking_id,
            {
              temperature_c: temperature ? Number(temperature) : undefined,
              note: "Đã đến phòng xét nghiệm",
            },
            { by: "booking" },
          )
        : await arriveAtLab(auth, selectedId, {
            temperature_c: temperature ? Number(temperature) : undefined,
            note: "Đã đến phòng xét nghiệm",
          });
      const sid = result.synthetic_specimen_id || String(result.sample_tracking?.sample_code ?? "");
      if (sid) setSpecimenId(sid);
      setMessage(`Đã đến phòng xét nghiệm${sid ? ` — mẫu ${sid}` : ""}.`);
      await refreshDetail(selectedId);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <SectionHeader
        title="Lấy mẫu & vận chuyển"
        description="Xác minh → quét mã vạch → lấy mẫu → bàn giao/vận chuyển → đến phòng xét nghiệm."
        actions={
          <Link href="/app/collector/queue" className="text-sm font-medium text-sky-700 hover:underline">
            Quay lại hàng đợi
          </Link>
        }
      />

      <div className="flex flex-wrap gap-2">
        {STEPS.map((label, index) => (
          <button
            key={label}
            type="button"
            onClick={() => setStep(index)}
            className={`rounded-lg px-3 py-1.5 text-sm ${
              step === index ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-700"
            }`}
          >
            {index + 1}. {label}
          </button>
        ))}
      </div>

      {message ? (
        <p className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          {message}
          {specimenId ? <span className="ml-2 font-mono text-xs">({specimenId})</span> : null}
        </p>
      ) : null}

      <DataState loading={loading} error={error} empty={!loading && !detail} emptyLabel="Không có ca lấy mẫu nào trong hàng đợi.">
        <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
          <aside className="space-y-2 rounded-xl border border-slate-200 bg-white p-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Hàng đợi</p>
            {queue.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => void onSelect(item.id)}
                className={`block w-full rounded-lg px-3 py-2 text-left text-sm ${
                  selectedId === item.id ? "bg-slate-900 text-white" : "hover:bg-slate-50"
                }`}
              >
                <div className="font-medium">{item.job_info?.patient_name || item.booking?.patient_name || "Bệnh nhân"}</div>
                <div className={selectedId === item.id ? "text-slate-300" : "text-slate-500"}>
                  {item.status}
                </div>
              </button>
            ))}
          </aside>

          <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
            {detail ? (
              <>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h3 className="text-base font-semibold text-slate-900">
                      {detail.job_info?.patient_name || detail.booking?.patient_name || "Specimen"}
                    </h3>
                    <p className="text-sm text-slate-600">
                      {detail.booking?.booking_code} · expected{" "}
                      <span className="font-mono">{detail.expected_barcode || "—"}</span>
                    </p>
                  </div>
                  <StatusPill status={detail.status} />
                </div>

                <JobInfoCard info={detail.job_info} />

                {step === 0 ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Tên bệnh nhân</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={patientName}
                        onChange={(e) => setPatientName(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Mã đặt lịch / mã đơn</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={bookingCode}
                        onChange={(e) => setBookingCode(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm sm:col-span-2">
                      <span className="mb-1 block text-slate-600">Quét mã vạch / QR</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono"
                        value={scannedBarcode}
                        onChange={(e) => setScannedBarcode(e.target.value)}
                        placeholder="Quét hoặc nhập mã vạch"
                      />
                    </label>
                    <div className="sm:col-span-2">
                      <Button disabled={!canWrite || busy} onClick={() => void onVerify()}>
                        Xác minh bệnh nhân & đơn
                      </Button>
                    </div>
                  </div>
                ) : null}

                {step === 1 ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Loại mẫu</span>
                      <select
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={specimenType}
                        onChange={(e) => setSpecimenType(e.target.value)}
                      >
                        <option value="BLOOD">Máu</option>
                        <option value="URINE">Nước tiểu</option>
                        <option value="SWAB">Dịch quệt (swab)</option>
                        <option value="OTHER">Khác</option>
                      </select>
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Nơi lấy mẫu</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={location}
                        onChange={(e) => setLocation(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm sm:col-span-2">
                      <span className="mb-1 block text-slate-600">Mã vạch (bắt buộc)</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 font-mono"
                        value={scannedBarcode}
                        onChange={(e) => setScannedBarcode(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm sm:col-span-2">
                      <span className="mb-1 block text-slate-600">Ghi chú (không bắt buộc)</span>
                      <textarea
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        rows={2}
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                      />
                    </label>
                    <div className="flex flex-wrap gap-2 sm:col-span-2">
                      <Button disabled={!canWrite || busy} onClick={() => void onCollect()}>
                        Ghi nhận đã lấy mẫu
                      </Button>
                    </div>
                    <div className="rounded-lg border border-rose-100 bg-rose-50/60 p-3 sm:col-span-2">
                      <p className="mb-2 text-sm font-medium text-rose-800">Mẫu không đạt chất lượng</p>
                      <div className="grid gap-2 sm:grid-cols-2">
                        <select
                          className="rounded-lg border border-rose-200 px-3 py-2 text-sm"
                          value={qualityStatus}
                          onChange={(e) => setQualityStatus(e.target.value)}
                        >
                          {QUALITY_REJECTION_OPTIONS.map((opt) => (
                            <option key={opt.value} value={opt.value}>
                              {REJECT_VI[opt.value] ?? opt.label}
                            </option>
                          ))}
                        </select>
                        <input
                          className="rounded-lg border border-rose-200 px-3 py-2 text-sm"
                          placeholder="Lý do từ chối"
                          value={rejectReason}
                          onChange={(e) => setRejectReason(e.target.value)}
                        />
                      </div>
                      <Button
                        className="mt-2"
                        size="sm"
                        variant="outline"
                        disabled={!canWrite || busy}
                        onClick={() => void onReject()}
                      >
                        Từ chối & yêu cầu lấy lại
                      </Button>
                    </div>
                  </div>
                ) : null}

                {step === 2 ? (
                  <div className="grid gap-3 sm:grid-cols-3">
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Nhiệt độ °C</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={temperature}
                        onChange={(e) => setTemperature(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Quãng đường (km)</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={distance}
                        onChange={(e) => setDistance(e.target.value)}
                      />
                    </label>
                    <label className="block text-sm">
                      <span className="mb-1 block text-slate-600">Thời gian dự kiến (phút)</span>
                      <input
                        className="w-full rounded-lg border border-slate-300 px-3 py-2"
                        value={eta}
                        onChange={(e) => setEta(e.target.value)}
                      />
                    </label>
                    <div className="sm:col-span-3">
                      <Button disabled={!canWrite || busy} onClick={() => void onDispatch()}>
                        Xuất phát & bàn giao
                      </Button>
                    </div>
                    <dl className="grid gap-2 text-sm text-slate-600 sm:col-span-3 sm:grid-cols-2">
                      <div>
                        <dt className="font-medium text-slate-800">Đã lấy</dt>
                        <dd>{detail.picked_up_at || "—"}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-800">Đã xuất phát</dt>
                        <dd>{detail.dispatched_at || "—"}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-800">Bàn giao</dt>
                        <dd>{detail.handoff_at || "—"}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-slate-800">Xe / tài xế</dt>
                        <dd>
                          {detail.vehicle_id || "—"} / {detail.driver_id || detail.collector_id || "—"}
                        </dd>
                      </div>
                    </dl>
                  </div>
                ) : null}

                {step === 3 ? (
                  <div className="space-y-3">
                    <p className="text-sm text-slate-600">
                      Xác nhận mẫu đã đến phòng xét nghiệm. Bước này dừng ở lúc mẫu đến — phòng xét nghiệm
                      accession/testing is out of scope for Sample Collection.
                    </p>
                    <Button disabled={!canWrite || busy || detail.status === "RECEIVED"} onClick={() => void onLabArrive()}>
                      {detail.status === "RECEIVED" ? "Đã ở phòng xét nghiệm" : "Xác nhận đã đến phòng xét nghiệm"}
                    </Button>
                    {detail.arrived_at_lab ? (
                      <p className="text-sm text-emerald-700">Arrived: {detail.arrived_at_lab}</p>
                    ) : null}
                  </div>
                ) : null}
              </>
            ) : null}
          </section>
        </div>
      </DataState>
    </div>
  );
}

export default function CollectorWorkflowPage() {
  return (
    <AppShell title="Lấy mẫu & vận chuyển" workspacePath="/app/collector">
      <Suspense fallback={<p className="text-sm text-slate-500">Đang tải quy trình…</p>}>
        <CollectorWorkflowPanel />
      </Suspense>
    </AppShell>
  );
}
