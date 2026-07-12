"use client";

import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";
import { normalizeApiError } from "@/lib/errors";
import type { PaginatedResult } from "@/lib/api/resources";

export type PilotColumn<T> = {
  key: string;
  label: string;
  render: (row: T) => string;
};

function PilotListPanel<T extends Record<string, unknown>>({
  title,
  columns,
  emptyLabel,
  searchPlaceholder,
  fetchPage,
  accessToken,
  organizationId,
  permissionDenied,
}: {
  title: string;
  columns: PilotColumn<T>[];
  emptyLabel: string;
  searchPlaceholder?: string;
  fetchPage: (
    token: string,
    organizationId: string,
    query: string,
    page: number,
  ) => Promise<PaginatedResult<T>>;
  accessToken: string;
  organizationId: string;
  permissionDenied: boolean;
}) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<T[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [correlationId, setCorrelationId] = useState<string | undefined>();
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    if (permissionDenied) return;

    let cancelled = false;

    void fetchPage(accessToken, organizationId, query, page)
      .then((result) => {
        if (cancelled) return;
        setRows(result.items);
        setTotal(result.total);
        setLoading(false);
        setError(null);
      })
      .catch((fetchError) => {
        if (cancelled) return;
        setRows([]);
        setError(normalizeApiError(fetchError));
        setLoading(false);
        if (fetchError && typeof fetchError === "object" && "correlationId" in fetchError) {
          setCorrelationId(String((fetchError as { correlationId?: string }).correlationId));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [accessToken, organizationId, query, page, fetchPage, retryCount, permissionDenied]);

  if (permissionDenied) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
        You do not have permission to view this data.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-900">{title}</h2>
          <p className="text-sm text-slate-500">{total} record(s)</p>
        </div>
        {searchPlaceholder ? (
          <Input
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(1);
            }}
            placeholder={searchPlaceholder}
            className="max-w-sm"
          />
        ) : null}
      </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-12 animate-pulse rounded-lg bg-slate-100" />
          ))}
        </div>
      ) : null}

      {error ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <p>{error}</p>
          {correlationId ? (
            <p className="mt-2 text-xs text-amber-700">Reference: {correlationId}</p>
          ) : null}
          <Button size="sm" className="mt-3" onClick={() => setRetryCount((n) => n + 1)}>
            Retry
          </Button>
        </div>
      ) : null}

      {!loading && !error && rows.length === 0 ? (
        <div className="rounded-xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">
          {emptyLabel}
        </div>
      ) : null}

      {!loading && !error && rows.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-slate-600">
              <tr>
                {columns.map((column) => (
                  <th key={column.key} className="px-4 py-3 font-medium">
                    {column.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr
                  key={String(row.id ?? row.patient_code ?? row.order_code ?? index)}
                  className="border-b border-slate-100"
                >
                  {columns.map((column) => (
                    <td key={column.key} className="px-4 py-3 text-slate-700">
                      {column.render(row)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

export function PilotListPage<T extends Record<string, unknown>>({
  title,
  workspacePath,
  permission,
  columns,
  emptyLabel,
  searchPlaceholder,
  fetchPage,
}: {
  title: string;
  workspacePath: string;
  permission?: string;
  columns: PilotColumn<T>[];
  emptyLabel: string;
  searchPlaceholder?: string;
  fetchPage: (
    token: string,
    organizationId: string,
    query: string,
    page: number,
  ) => Promise<PaginatedResult<T>>;
}) {
  const { accessToken, activeOrganizationId, can } = useAuth();
  const permissionDenied = Boolean(permission && !can(permission));

  return (
    <AppShell title={title} workspacePath={workspacePath}>
      {accessToken && activeOrganizationId ? (
        <PilotListPanel
          key={`${accessToken}:${activeOrganizationId}:${workspacePath}`}
          title={title}
          columns={columns}
          emptyLabel={emptyLabel}
          searchPlaceholder={searchPlaceholder}
          fetchPage={fetchPage}
          accessToken={accessToken}
          organizationId={activeOrganizationId}
          permissionDenied={permissionDenied}
        />
      ) : (
        <p className="text-sm text-slate-500">Loading session…</p>
      )}
    </AppShell>
  );
}
