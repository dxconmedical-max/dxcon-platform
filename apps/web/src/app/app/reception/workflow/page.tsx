"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import {
  fetchReceptionOrder,
  type ReceptionOrderCreate,
  type ReceptionOrderPricing,
} from "@/lib/api/reception";
import { getBookingRequest, setBookingStatus, type BookingRequestItem } from "@/lib/api/publicBooking";
import { normalizeApiError } from "@/lib/errors";

import { SectionHeader } from "../_components/ui";
import { ConsentPanel } from "./ConsentPanel";
import {
  CatalogSelectStep,
  CollectionRequestStep,
  OrderConfirmationStep,
  PatientStep,
  ReviewPricingStep,
  type CatalogSelection,
  type CollectionRequestDraft,
  type SelectedPatient,
} from "./Milestone1Steps";
import { PaymentStep } from "./OrderSteps";

const SLOT_WINDOWS: Record<string, string> = {
  MORNING: "08:00–12:00",
  AFTERNOON: "13:00–17:00",
  ANYTIME: "08:00–17:00",
};

const STEPS = [
  "Bệnh nhân",
  "Xét nghiệm",
  "Yêu cầu thu mẫu",
  "Kiểm tra và tính giá",
  "Xác nhận",
] as const;

function ReceptionMilestone1Panel() {
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const searchParams = useSearchParams();
  const patientParam = searchParams.get("patient") ?? undefined;
  const orderParam = searchParams.get("order") ?? undefined;
  const bookingParam = searchParams.get("booking") ?? undefined;

  /** UI steps: 0 Patient, 1 Tests, 2 Collection request, 3 Review (create), 4 Confirmation. */
  const [step, setStep] = useState(0);
  const [patient, setPatient] = useState<SelectedPatient | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selection, setSelection] = useState<CatalogSelection | null>(null);
  const [collectionRequest, setCollectionRequest] = useState<CollectionRequestDraft | null>(null);
  const [orderRef, setOrderRef] = useState<string | null>(null);
  const [pricing, setPricing] = useState<ReceptionOrderPricing | null>(null);
  const [order, setOrder] = useState<ReceptionOrderCreate["order"] | null>(null);
  const [confirmationTick, setConfirmationTick] = useState(0);
  const [reopenError, setReopenError] = useState<string | null>(null);
  const [reopening, setReopening] = useState(Boolean(orderParam));

  // Website booking request being turned into a real order (patient + home-collection request prefilled).
  const [booking, setBooking] = useState<BookingRequestItem | null>(null);
  const [bookingLoading, setBookingLoading] = useState(Boolean(bookingParam));
  const [bookingError, setBookingError] = useState<string | null>(null);

  useEffect(() => {
    if (!bookingParam || !accessToken) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      void getBookingRequest({ token: accessToken, organizationId: activeOrganizationId }, bookingParam)
        .then((b) => {
          if (cancelled) return;
          setBooking(b);
          setCollectionRequest({
            mode: "HOME_COLLECTION",
            specimen_type: "BLOOD",
            pickup_address: b.address,
            pickup_province: /h[ồo]\s*ch[íi]\s*minh/i.test(b.address) ? "Hồ Chí Minh" : "",
            pickup_district: b.district ?? "",
            contact_person: b.full_name,
            contact_phone: b.phone,
            requested_date: b.preferred_date ?? "",
            requested_time_window: SLOT_WINDOWS[b.preferred_slot] ?? "",
            notes: b.note ?? "",
          });
        })
        .catch((err) => {
          if (!cancelled) setBookingError(normalizeApiError(err));
        })
        .finally(() => {
          if (!cancelled) setBookingLoading(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [bookingParam, accessToken, activeOrganizationId]);

  const onQueryChange = useCallback((q: string) => setSearchQuery(q), []);

  const canWrite =
    can("reception.write") ||
    can("orders.create") ||
    can("patients.create") ||
    ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN", "PARTNER_RECEPTION"].includes(
      role ?? "",
    );

  const badgeIndex = step;

  useEffect(() => {
    if (!orderParam || !accessToken) {
      return;
    }
    let cancelled = false;
    const timer = window.setTimeout(() => {
      if (cancelled) return;
      setReopening(true);
      setReopenError(null);
      void fetchReceptionOrder(
        { token: accessToken, organizationId: activeOrganizationId, timeoutMs: 30_000 },
        orderParam,
      )
        .then((result) => {
          if (cancelled) return;
          const row = result.order as Record<string, unknown>;
          setPatient({
            patientCode: String(row.patient_code ?? row.patient_id ?? ""),
            patientName: String(row.patient_name ?? row.patient_code ?? "Patient"),
          });
          setOrderRef(String(row.order_code ?? orderParam));
          setPricing(result.pricing);
          setOrder(result.order);
          setStep(4);
        })
        .catch((err) => {
          if (!cancelled) setReopenError(normalizeApiError(err));
        })
        .finally(() => {
          if (!cancelled) setReopening(false);
        });
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [orderParam, accessToken, activeOrganizationId]);

  function reset() {
    setStep(0);
    setPatient(null);
    setSelection(null);
    setCollectionRequest(null);
    setOrderRef(null);
    setPricing(null);
    setOrder(null);
    setReopenError(null);
    setBooking(null);
  }

  if (!accessToken) {
    return <p className="text-sm text-slate-500">Đang chờ phiên đăng nhập…</p>;
  }

  if (!canWrite) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Cần quyền ghi của tiếp nhận để tạo bệnh nhân và đơn.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Tiếp nhận — Bệnh nhân, xét nghiệm, yêu cầu thu mẫu và đơn"
        description="Ghi nhận yêu cầu thu mẫu trước khi tính giá và tạo đơn."
        actions={
          step > 0 ? (
            <Button size="sm" variant="outline" onClick={reset}>
              Làm lại từ đầu
            </Button>
          ) : (
            <Link href="/app/reception">
              <Button size="sm" variant="ghost">
                Trang chủ
              </Button>
            </Link>
          )
        }
      />

      <div className="flex flex-wrap gap-2" aria-label="Các bước tạo đơn tiếp nhận">
        {STEPS.map((label, index) => {
          const active = index === badgeIndex;
          const done = index < badgeIndex;
          return (
            <Badge key={label} tone={active ? "info" : done ? "success" : "default"}>
              {index + 1}. {label}
            </Badge>
          );
        })}
      </div>

      {reopening ? <p className="text-sm text-slate-500">Đang mở lại đơn…</p> : null}
      {reopenError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
          {reopenError}
        </div>
      ) : null}

      {booking ? (
        <div className="rounded-xl border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900">
          Đang tạo đơn từ yêu cầu đặt lịch {booking.reference} của {booking.full_name} ({booking.phone}). Thông tin thu mẫu tại nhà đã điền sẵn, anh/chị chọn bệnh nhân, xét nghiệm rồi tạo đơn. Đơn sẽ hiện cho nhân viên thu mẫu.
        </div>
      ) : null}
      {bookingError ? (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{bookingError}</div>
      ) : null}

      {!reopening && !bookingLoading && step === 0 ? (
        <PatientStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          initialQuery={patientParam ?? booking?.phone}
          prefill={booking ? { full_name: booking.full_name, phone: booking.phone, address: booking.address, email: booking.email ?? undefined } : undefined}
          preservedQuery={searchQuery || undefined}
          onQueryChange={onQueryChange}
          onSelect={(selected) => {
            setPatient(selected);
            setStep(1);
          }}
        />
      ) : null}

      {!reopening && (step === 1 || step === 3) && patient ? (
        <ConsentPanel
          key={patient.patientCode}
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patientCode={patient.patientCode}
        />
      ) : null}

      {!reopening && step === 1 && patient ? (
        <CatalogSelectStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          initial={selection}
          onBack={() => setStep(0)}
          onContinue={(next) => {
            setSelection(next);
            setStep(2);
          }}
        />
      ) : null}

      {!reopening && step === 2 && patient && selection ? (
        <CollectionRequestStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          selection={selection}
          initial={collectionRequest}
          onBack={() => setStep(1)}
          onContinue={(draft) => {
            setCollectionRequest(draft);
            setStep(3);
          }}
        />
      ) : null}

      {!reopening && step === 3 && patient && selection && collectionRequest ? (
        <ReviewPricingStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          selection={selection}
          collectionRequest={collectionRequest}
          onBack={() => setStep(2)}
          onCreated={({ orderRef: ref, pricing: nextPricing, order: nextOrder }) => {
            setOrderRef(ref);
            setPricing(nextPricing);
            setOrder(nextOrder);
            setStep(4);
            if (booking) {
              // Link the website request to the new order; failure here must not disturb the order flow.
              void setBookingStatus(
                { token: accessToken, organizationId: activeOrganizationId },
                booking.id,
                "SCHEDULED",
                undefined,
                ref,
              ).catch(() => undefined);
            }
          }}
        />
      ) : null}

      {!reopening && step === 4 && patient && orderRef && pricing && order ? (
        <OrderConfirmationStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          order={order}
          onCreateAnother={reset}
          refreshSignal={confirmationTick}
        />
      ) : null}

      {!reopening && step === 4 && patient && orderRef && pricing && order ? (
        <PaymentStep
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          patient={patient}
          orderRef={orderRef}
          pricing={pricing}
          order={order}
          onReset={reset}
          onPaymentRecorded={() => setConfirmationTick((n) => n + 1)}
        />
      ) : null}
    </div>
  );
}

export default function ReceptionWorkflowPage() {
  return (
    <AppShell title="Đơn tiếp nhận" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Đang tải…</p>}>
        <ReceptionMilestone1Panel />
      </Suspense>
    </AppShell>
  );
}
