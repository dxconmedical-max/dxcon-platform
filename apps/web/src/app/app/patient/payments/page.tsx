"use client";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import { fetchPatientInvoices, type PatientInvoice } from "@/lib/api/patient-portal";

function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat("vi-VN", { style: "currency", currency }).format(amount);
  } catch {
    return `${amount.toLocaleString()} ${currency}`;
  }
}

function PaymentsPanel({ accessToken, organizationId }: WorkspaceContext) {
  const state = useSourcedData<PatientInvoice[]>(
    () => fetchPatientInvoices({ token: accessToken, organizationId }),
    [accessToken, organizationId],
  );
  const rows = state.data ?? [];
  const outstanding = rows
    .filter((r) => r.status.toUpperCase() !== "PAID")
    .reduce((sum, r) => sum + r.amount, 0);

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Payments & invoices"
        description={
          outstanding > 0
            ? `Outstanding balance: ${formatMoney(outstanding, rows[0]?.currency ?? "VND")}`
            : "Invoice history and receipts."
        }
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={rows.length === 0}
        emptyLabel="No invoices yet."
        onRetry={state.reload}
      >
        <SimpleTable<PatientInvoice>
          rows={rows}
          rowKey={(row) => row.invoice_no}
          columns={[
            { key: "invoice", label: "Invoice", render: (r) => r.invoice_no },
            { key: "description", label: "Description", render: (r) => r.description ?? "—" },
            { key: "issued", label: "Issued", render: (r) => r.issued_at },
            { key: "amount", label: "Amount", render: (r) => formatMoney(r.amount, r.currency) },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
          ]}
        />
      </DataState>
    </div>
  );
}

export default function PatientPaymentsPage() {
  return (
    <WorkspaceScreen title="Payments" workspacePath="/app/patient" permission="portal.patient.read">
      {(ctx) => <PaymentsPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
