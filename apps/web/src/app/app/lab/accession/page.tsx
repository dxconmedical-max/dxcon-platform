"use client";

import { useState } from "react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import { ScannerPlaceholder, SectionHeader } from "@/components/workspace/primitives";
import { accessionSpecimen } from "@/lib/api/lab";
import type { DataSource } from "@/lib/api/adapter";
import { normalizeApiError } from "@/lib/errors";

function AccessionPanel({ accessToken, organizationId, userName }: WorkspaceContext) {
  const [barcode, setBarcode] = useState("");
  const [rack, setRack] = useState("");
  const [shelf, setShelf] = useState("");
  const [batch, setBatch] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [source, setSource] = useState<DataSource | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await accessionSpecimen(
        { token: accessToken, organizationId },
        { barcode_value: barcode.trim(), rack, shelf, batch, operator: userName },
      );
      setResult(response.value);
      setSource(response.source);
      setBarcode("");
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader title="Accession" description="Receive specimen, verify barcode, assign storage." />

      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <Card className="space-y-4">
          <div>
            <Label htmlFor="barcode">Specimen barcode *</Label>
            <Input id="barcode" value={barcode} onChange={(e) => setBarcode(e.target.value)} placeholder="DXYYYYMMDD000001" />
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <Label htmlFor="rack">Rack</Label>
              <Input id="rack" value={rack} onChange={(e) => setRack(e.target.value)} placeholder="R1" />
            </div>
            <div>
              <Label htmlFor="shelf">Shelf</Label>
              <Input id="shelf" value={shelf} onChange={(e) => setShelf(e.target.value)} placeholder="S2" />
            </div>
            <div>
              <Label htmlFor="batch">Batch</Label>
              <Input id="batch" value={batch} onChange={(e) => setBatch(e.target.value)} placeholder="B3" />
            </div>
          </div>
          <Button onClick={submit} disabled={!barcode.trim() || submitting}>
            {submitting ? "Accessioning…" : "Receive & accession"}
          </Button>
          {error ? <p className="text-sm text-rose-600">{error}</p> : null}
          {result ? (
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
              <div className="flex items-center gap-2">
                <span>Accession {String(result.accession_number ?? "—")} recorded.</span>
                {source === "sample" ? <Badge className="bg-amber-100 text-amber-800">Sample</Badge> : <Badge tone="success">Live</Badge>}
              </div>
            </div>
          ) : null}
        </Card>

        <ScannerPlaceholder label="Scan barcode at accession" onSimulate={() => setBarcode("DX20260712000001")} />
      </div>
    </div>
  );
}

export default function LabAccessionPage() {
  return (
    <WorkspaceScreen title="Accession" workspacePath="/app/lab" permission="lab.read">
      {(ctx) => <AccessionPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
