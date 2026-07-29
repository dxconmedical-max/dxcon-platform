"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import {
  fetchMedicalQueue,
  medicalReject,
  medicalReopen,
  medicalValidate,
  type LabQueueRow,
} from "@/lib/api/labWorkflow";

import { DataState, SectionHeader, SimpleTable } from "../../reception/_components/ui";

export default function DoctorMedicalValidationPage() {
  const { accessToken, activeOrganizationId, role } = useAuth();
  const auth = useMemo(
    () => ({ token: accessToken, organizationId: activeOrganizationId }),
    [accessToken, activeOrganizationId],
  );
  const canMedical = ["DOCTOR", "ADMIN", "SUPER_ADMIN", "SYSTEM_ADMIN"].includes(role ?? "");

  const [items, setItems] = useState<LabQueueRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accessToken) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchMedicalQueue(auth));
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, auth]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(
    orderCode: string,
    action: "approve" | "reject" | "reopen",
  ) {
    setBusy(orderCode);
    setError(null);
    setMessage(null);
    try {
      if (action === "approve") await medicalValidate(auth, orderCode, note || undefined);
      if (action === "reject") await medicalReject(auth, orderCode, note || undefined);
      if (action === "reopen") await medicalReopen(auth, orderCode, note || undefined);
      setMessage(`${action} completed for ${orderCode}`);
      await load();
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setBusy(null);
    }
  }

  return (
    <AppShell title="Medical validation" workspacePath="/app/doctor">
      <div className="space-y-5">
        <SectionHeader
          title="Medical validation inbox"
          description="Approve, reject, or reopen results awaiting doctor sign-off. Actions write timeline and audit logs."
          actions={
            <div className="flex gap-2">
              <Link href="/app/lab/release" className="self-center text-sm text-sky-700 hover:underline">
                Release board
              </Link>
              <Button size="sm" variant="outline" onClick={() => void load()}>
                Refresh
              </Button>
            </div>
          }
        />
        {!canMedical ? (
          <p className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
            Doctor or admin role required for medical validation actions.
          </p>
        ) : null}
        <div>
          <Label htmlFor="doctor-note">Note (optional)</Label>
          <Input id="doctor-note" value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        <DataState
          loading={loading}
          error={error}
          empty={!loading && items.length === 0}
          emptyLabel="No results pending medical review."
          onRetry={() => void load()}
        >
          <SimpleTable
            rows={items}
            rowKey={(row) => row.order_code}
            columns={[
              { key: "order", label: "Order", render: (row) => row.order_code },
              {
                key: "patient",
                label: "Patient",
                render: (row) => row.patient_name || row.patient || "—",
              },
              { key: "status", label: "Status", render: (row) => row.status || "—" },
              {
                key: "actions",
                label: "Actions",
                render: (row) => (
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "approve")}
                    >
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "reject")}
                    >
                      Reject
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={!canMedical || busy === row.order_code}
                      onClick={() => void run(row.order_code, "reopen")}
                    >
                      Reopen
                    </Button>
                    <Link
                      href={`/app/lab/workflow?order=${encodeURIComponent(row.order_code)}`}
                      className="self-center text-xs text-sky-700 hover:underline"
                    >
                      Open lab
                    </Link>
                  </div>
                ),
              },
            ]}
          />
        </DataState>
      </div>
    </AppShell>
  );
}
