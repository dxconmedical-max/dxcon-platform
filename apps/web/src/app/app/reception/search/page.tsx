"use client";

import { useState } from "react";
import { Search } from "lucide-react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  DataState,
  ScannerPlaceholder,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { searchReception, type QueueEntry } from "@/lib/api/reception";
import type { DataSource } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

function SearchPanel({ accessToken, organizationId }: WorkspaceContext) {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<QueueEntry[]>([]);
  const [source, setSource] = useState<DataSource | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(term: string) {
    if (!term.trim()) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReception({ token: accessToken, organizationId }, term.trim());
      setRows(result.value);
      setSource(result.source);
    } catch (err) {
      setRows([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Booking & patient search"
        description="Find patients and bookings by name, code, or reference."
        source={source ?? undefined}
      />

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void runSearch(query);
            }}
          >
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search patient name, code, or booking reference"
            />
            <Button type="submit" disabled={!query.trim() || loading}>
              <Search className="h-4 w-4" />
              Search
            </Button>
          </form>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={rows.length === 0}
              emptyLabel="No matches found."
              onRetry={() => void runSearch(query)}
            >
              <SimpleTable<QueueEntry>
                rows={rows}
                rowKey={(row) => row.id}
                columns={[
                  { key: "patient", label: "Patient", render: (r) => r.patient_name },
                  { key: "code", label: "Code", render: (r) => r.patient_code ?? "—" },
                  { key: "service", label: "Service", render: (r) => r.service ?? "—" },
                  { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
                ]}
              />
            </DataState>
          ) : (
            <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Enter a search term or scan a QR code to begin.
            </p>
          )}
        </div>

        <ScannerPlaceholder
          label="Scan booking QR"
          onSimulate={() => {
            setQuery("Le Van C");
            void runSearch("Le Van C");
          }}
        />
      </div>
    </div>
  );
}

export default function ReceptionSearchPage() {
  return (
    <WorkspaceScreen title="Search" workspacePath="/app/reception" permission="reception.read">
      {(ctx) => <SearchPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
