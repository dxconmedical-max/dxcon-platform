"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { searchReceptionPatients, type ReceptionPatient } from "@/lib/api/reception";
import { isRequestAborted, normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

const SEARCH_DEBOUNCE_MS = 350;

function SearchPanel() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { accessToken, activeOrganizationId, can, role } = useAuth();
  const initialQ = searchParams.get("q") ?? "";
  const [query, setQuery] = useState(initialQ);
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(Boolean(initialQ.trim()));
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const canRead =
    can("reception.read") ||
    can("patients.read") ||
    can("reception.write") ||
    ["RECEPTION", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN", "PARTNER_RECEPTION"].includes(
      role ?? "",
    );

  async function runSearch(term: string) {
    if (!accessToken) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        { token: accessToken, organizationId: activeOrganizationId, signal: controller.signal },
        term.trim(),
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
  }

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const next = query.trim()
        ? `/app/reception/search?q=${encodeURIComponent(query.trim())}`
        : "/app/reception/search";
      router.replace(next);
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [query, router]);

  useEffect(() => {
    if (!query.trim()) {
      abortRef.current?.abort();
      setLoading(false);
      return;
    }
    const timer = window.setTimeout(() => void runSearch(query), SEARCH_DEBOUNCE_MS);
    return () => {
      window.clearTimeout(timer);
      abortRef.current?.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, accessToken, activeOrganizationId]);

  if (!canRead) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        Cần quyền xem của tiếp nhận để tìm bệnh nhân.
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Tìm bệnh nhân"
        description="Tìm bệnh nhân theo số điện thoại, mã bệnh nhân, CCCD hoặc họ tên."
        actions={
          <>
            <Link href={`/app/reception/register${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`}>
              <Button size="sm" variant="outline">
                Đăng ký
              </Button>
            </Link>
            <Link href="/app/reception/workflow">
              <Button size="sm">Tạo đơn</Button>
            </Link>
          </>
        }
      />
      <Input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Số điện thoại, mã bệnh nhân, CCCD hoặc tên"
        aria-label="Tìm bệnh nhân"
      />

      {searched ? (
        <DataState
          loading={loading}
          error={error}
          empty={!loading && patients.length === 0}
          emptyLabel="Không tìm thấy bệnh nhân."
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
                  <Link
                    href={`/app/reception/workflow?patient=${encodeURIComponent(row.patient_code)}`}
                  >
                    <Button size="sm" variant="outline">
                      Đơn
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </DataState>
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          Nhập để tìm kiếm. Nội dung tìm sẽ được giữ lại khi mở trang đăng ký.
        </p>
      )}
    </div>
  );
}

export default function ReceptionSearchPage() {
  return (
    <AppShell title="Tìm bệnh nhân" workspacePath="/app/reception">
      <Suspense fallback={<p className="text-sm text-slate-500">Đang tải…</p>}>
        <SearchPanel />
      </Suspense>
    </AppShell>
  );
}
