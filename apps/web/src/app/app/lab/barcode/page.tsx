"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import {
  DataState,
  QrPanel,
  ScannerPlaceholder,
  SectionHeader,
  StatusPill,
} from "@/components/workspace/primitives";
import { verifySpecimenBarcode } from "@/lib/api/lab";
import type { LimsSpecimen } from "@/lib/api/lab";
import type { DataSource } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

function BarcodePanel({ accessToken, organizationId }: WorkspaceContext) {
  const [value, setValue] = useState("");
  const [specimen, setSpecimen] = useState<LimsSpecimen | null>(null);
  const [source, setSource] = useState<DataSource | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function lookup(barcode: string) {
    if (!barcode.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await verifySpecimenBarcode(
        { token: accessToken, organizationId },
        barcode.trim(),
      );
      setSource(result.source);
      setSpecimen(result.value.specimen ?? null);
      if (!result.value.valid) setError("Barcode not found.");
    } catch (err) {
      setSpecimen(null);
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="Barcode viewer" description="Verify specimen barcodes (Code128 and QR)." source={source ?? undefined} />

      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="space-y-4">
          <form
            className="flex gap-2"
            onSubmit={(event) => {
              event.preventDefault();
              void lookup(value);
            }}
          >
            <Input
              value={value}
              onChange={(event) => setValue(event.target.value)}
              placeholder="Scan or enter barcode (DXYYYYMMDD000001)"
            />
            <Button type="submit" disabled={!value.trim() || loading}>
              Verify
            </Button>
          </form>

          <DataState loading={loading} error={error} empty={!specimen && !loading && !error} emptyLabel="Enter a barcode to view details.">
            {specimen ? (
              <div className="grid gap-4 md:grid-cols-[auto_1fr] md:items-start">
                <QrPanel payload={specimen.barcode} caption={specimen.human_readable} />
                <div className="space-y-2 rounded-xl border border-slate-200 bg-white p-4 text-sm">
                  <p><span className="text-slate-500">Human readable:</span> {specimen.human_readable}</p>
                  <p><span className="text-slate-500">Order:</span> {specimen.order_code ?? "—"}</p>
                  <p><span className="text-slate-500">Container:</span> {specimen.container_type ?? "—"}</p>
                  <p className="flex items-center gap-2">
                    <span className="text-slate-500">Status:</span>
                    <StatusPill status={specimen.status} />
                  </p>
                </div>
              </div>
            ) : null}
          </DataState>
        </div>

        <ScannerPlaceholder label="Scan specimen barcode" onSimulate={() => { setValue("DX20260712000001"); void lookup("DX20260712000001"); }} />
      </div>
    </div>
  );
}

export default function LabBarcodePage() {
  return (
    <WorkspaceScreen title="Barcode viewer" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <BarcodePanel {...ctx} />}
    </WorkspaceScreen>
  );
}
