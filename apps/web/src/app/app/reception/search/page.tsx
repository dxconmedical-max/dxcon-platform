"use client";

import Link from "next/link";
import { useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { searchReceptionPatients, type ReceptionPatient } from "@/lib/api/reception";
import { normalizeApiError } from "@/lib/errors";

import { DataState, SectionHeader, SimpleTable } from "../_components/ui";

function SearchPanel() {
  const { accessToken, activeOrganizationId } = useAuth();
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<ReceptionPatient[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    if (!accessToken) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const result = await searchReceptionPatients(
        { token: accessToken, organizationId: activeOrganizationId },
        query.trim(),
      );
      setPatients(result.items);
    } catch (err) {
      setPatients([]);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-5">
      <SectionHeader
        title="Patient search"
        description="Search production patient records by code, name, phone, or national ID."
        actions={
          <>
            <Link href="/app/reception/register">
              <Button size="sm" variant="outline">
                Register
              </Button>
            </Link>
            <Link href="/app/reception/workflow">
              <Button size="sm">Create order</Button>
            </Link>
          </>
        }
      />
      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void runSearch();
        }}
      >
        <Input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Patient code, name, phone, or national ID"
        />
        <Button type="submit" disabled={loading || !accessToken}>
          Search
        </Button>
      </form>

      {searched ? (
        <DataState
          loading={loading}
          error={error}
          empty={patients.length === 0}
          emptyLabel="No patients found."
          onRetry={() => void runSearch()}
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
                  <Link href={`/app/reception/workflow?patient=${encodeURIComponent(row.patient_code)}`}>
                    <Button size="sm" variant="outline">
                      Order
                    </Button>
                  </Link>
                ),
              },
            ]}
          />
        </DataState>
      ) : (
        <p className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          Enter a search term to find patients.
        </p>
      )}
    </div>
  );
}

export default function ReceptionSearchPage() {
  return (
    <AppShell title="Patient search" workspacePath="/app/reception">
      <SearchPanel />
    </AppShell>
  );
}
