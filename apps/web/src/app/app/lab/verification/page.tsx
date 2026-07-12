"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import {
  fetchVerificationQueue,
  releaseResult,
  verifyResult,
  type VerificationItem,
} from "@/lib/api/lab";

function VerificationPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<VerificationItem[]>(
    () => fetchVerificationQueue({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState<string | null>(null);

  const rows = (state.data ?? []).map((item) =>
    overrides[item.order_code] ? { ...item, status: overrides[item.order_code] } : item,
  );

  async function verify(orderCode: string) {
    setBusy(orderCode);
    try {
      const result = await verifyResult({ token: accessToken, organizationId }, orderCode);
      setOverrides((prev) => ({ ...prev, [orderCode]: result.value.status }));
    } finally {
      setBusy(null);
    }
  }

  async function release(orderCode: string) {
    setBusy(orderCode);
    try {
      const result = await releaseResult({ token: accessToken, organizationId }, orderCode);
      setOverrides((prev) => ({ ...prev, [orderCode]: result.value.status }));
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Verification & release"
        description="Verify results, then release reports to clinicians and patients."
        source={state.source ?? undefined}
        actions={
          <Button size="sm" variant="outline" onClick={state.reload}>
            Refresh
          </Button>
        }
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="Nothing awaiting verification."
        onRetry={state.reload}
      >
        <SimpleTable<VerificationItem>
          rows={rows}
          rowKey={(row) => row.order_code}
          columns={[
            { key: "order", label: "Order", render: (r) => r.order_code },
            { key: "test", label: "Test", render: (r) => r.test ?? "—" },
            {
              key: "result",
              label: "Result",
              render: (r) =>
                r.abnormal ? (
                  <span className="inline-flex items-center gap-2">
                    <span className="font-medium text-rose-700">{r.result_value ?? "—"}</span>
                    <Badge className="bg-rose-100 text-rose-700">Abnormal</Badge>
                  </span>
                ) : (
                  <span className="text-slate-700">{r.result_value ?? "—"}</span>
                ),
            },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
            {
              key: "action",
              label: "",
              render: (r) => {
                const status = r.status.toUpperCase();
                if (status === "AWAITING_VERIFICATION") {
                  return (
                    <Button size="sm" disabled={busy === r.order_code} onClick={() => verify(r.order_code)}>
                      {busy === r.order_code ? "…" : "Verify"}
                    </Button>
                  );
                }
                if (status === "VERIFIED") {
                  return (
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={busy === r.order_code}
                      onClick={() => release(r.order_code)}
                    >
                      {busy === r.order_code ? "…" : "Release"}
                    </Button>
                  );
                }
                return <span className="text-xs text-emerald-700">Released</span>;
              },
            },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function LabVerificationPage() {
  return (
    <WorkspaceScreen title="Verification & release" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <VerificationPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
