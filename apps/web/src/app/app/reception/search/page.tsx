"use client";

import Link from "next/link";
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
} from "@/components/workspace/primitives";
import { searchReceptionPatients, type ReceptionPatient } from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

function SearchPanel({ accessToken, organizationId }: WorkspaceContext) {
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch(term: string) {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients({ token: accessToken, organizationId }, term.trim());
      setRows(result.items);
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
        title="Patient search"
        description="Find patients by code, name, phone, or national ID."
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
              placeholder="Patient code, name, phone, or national ID"
            />
            <Button type="submit" disabled={loading || !query.trim()}>
              <Search className="h-4 w-4" />
              Search
            </Button>
          </form>

          {searched ? (
            <DataState
              loading={loading}
              error={error}
              empty={rows.length === 0}
              emptyLabel="No patients found."
              onRetry={() => void runSearch(query)}
            >
              <SimpleTable<ReceptionPatient>
                rows={rows}
                rowKey={(row) => row.patient_code}
                columns={[
                  { key: "patient", label: "Patient", render: (row) => row.full_name },
                  { key: "code", label: "Code", render: (row) => row.patient_code },
                  { key: "phone", label: "Phone", render: (row) => row.phone ?? "—" },
                  { key: "nid", label: "National ID", render: (row) => row.national_id ?? "—" },
                  {
                    key: "action",
                    label: "",
                    render: (row) => (
                      <Link href={`/app/reception/workflow?patient=${encodeURIComponent(row.patient_code)}`}>
                        <Button size="sm" variant="outline">
                          Start order
                        </Button>
                      </Link>
                    ),
                  },
                ]}
              />
            </DataState>
          ) : (
            <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
              Enter a search term or scan a patient QR code to begin.
            </p>
          )}
        </div>

        <ScannerPlaceholder
          label="Scan patient QR"
          onSimulate={() => {
            setQuery("");
            void runSearch("");
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
