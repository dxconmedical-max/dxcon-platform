"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import { PenLine, Sparkles } from "lucide-react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input, Label } from "@/components/ui/Input";
import {
  DataState,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import {
  fetchDoctorReport,
  saveDoctorNote,
  signReport,
  type DoctorReport,
  type ReportAnalyte,
} from "@/lib/api/doctor";

function ReportPanel({
  reportCode,
  accessToken,
  organizationId,
  userName,
}: WorkspaceContext & { reportCode: string }) {
  const state = useSourcedData<DoctorReport>(
    () => fetchDoctorReport({ token: accessToken, organizationId }, reportCode),
    [accessToken, organizationId, reportCode],
  );
  const report = state.data;

  const [note, setNote] = useState("");
  const [noteMsg, setNoteMsg] = useState<string | null>(null);
  const [savingNote, setSavingNote] = useState(false);

  const [signer, setSigner] = useState(userName ?? "");
  const [signing, setSigning] = useState(false);
  const [signedStatus, setSignedStatus] = useState<string | null>(null);

  async function saveNote() {
    if (!report) return;
    setSavingNote(true);
    setNoteMsg(null);
    try {
      const result = await saveDoctorNote(
        { token: accessToken, organizationId },
        { patient_code: report.patient_code ?? report.patient_name, note_text: note },
      );
      setNoteMsg(result.value.message);
    } finally {
      setSavingNote(false);
    }
  }

  async function sign() {
    if (!report || !signer.trim()) return;
    setSigning(true);
    try {
      const result = await signReport(
        { token: accessToken, organizationId },
        { report_code: report.report_code, order_code: report.report_code, signer_name: signer.trim() },
      );
      setSignedStatus(result.value.status);
    } finally {
      setSigning(false);
    }
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title={`Report ${reportCode}`}
        description="Result viewer with abnormal highlighting and sign-off."
        source={state.source ?? undefined}
      />
      <DataState
        loading={state.loading}
        error={state.error}
        empty={!report}
        emptyLabel="Report not found."
        onRetry={state.reload}
      >
        {report ? (
          <div className="space-y-4">
            <Card className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <p className="text-xs text-slate-500">Patient</p>
                <p className="font-medium text-slate-900">{report.patient_name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Patient code</p>
                <p className="font-medium text-slate-900">{report.patient_code ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Collected</p>
                <p className="font-medium text-slate-900">{report.collected_at ?? "—"}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Status</p>
                <StatusPill status={signedStatus ?? report.status} />
              </div>
            </Card>

            <div>
              <h3 className="mb-2 text-sm font-semibold text-slate-900">Results</h3>
              <SimpleTable<ReportAnalyte>
                rows={report.analytes}
                rowKey={(row, index) => `${row.name}-${index}`}
                columns={[
                  {
                    key: "name",
                    label: "Analyte",
                    render: (r) => (
                      <span className={r.abnormal ? "font-medium text-rose-700" : "text-slate-700"}>
                        {r.name}
                      </span>
                    ),
                  },
                  {
                    key: "value",
                    label: "Value",
                    render: (r) => (
                      <span className={r.abnormal ? "font-semibold text-rose-700" : "text-slate-900"}>
                        {r.value}
                        {r.unit ? ` ${r.unit}` : ""}
                        {r.abnormal ? (
                          <Badge className="ml-2 bg-rose-100 text-rose-700">{r.flag ?? "Abnormal"}</Badge>
                        ) : null}
                      </span>
                    ),
                  },
                  { key: "reference", label: "Reference", render: (r) => r.reference || "—" },
                ]}
              />
            </div>

            <Card className="space-y-2 border-teal-200 bg-teal-50/40">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-teal-600" />
                <Badge tone="info">AI interpretation — requires clinician confirmation</Badge>
              </div>
              <p className="text-sm text-slate-700">
                {report.ai_interpretation ?? "AI interpretation is not available for this report yet."}
              </p>
            </Card>

            <Card className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-900">Clinical note</h3>
              <textarea
                value={note}
                onChange={(event) => setNote(event.target.value)}
                rows={3}
                placeholder="Add an interpretation or follow-up recommendation…"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
              />
              <div className="flex items-center gap-3">
                <Button size="sm" variant="outline" onClick={saveNote} disabled={!note.trim() || savingNote}>
                  {savingNote ? "Saving…" : "Save note"}
                </Button>
                {noteMsg ? <span className="text-xs text-slate-500">{noteMsg}</span> : null}
              </div>
            </Card>

            <Card className="space-y-3">
              <div className="flex items-center gap-2">
                <PenLine className="h-5 w-5 text-slate-700" />
                <h3 className="text-sm font-semibold text-slate-900">Electronic signature</h3>
              </div>
              <p className="text-xs text-slate-500">
                Signing approves this report. Handwritten/PIN signature capture is planned; sign-off maps to
                report approval on the backend.
              </p>
              {signedStatus ? (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                  Report signed by {signer} — status {signedStatus}.
                </div>
              ) : (
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                  <div className="flex-1">
                    <Label htmlFor="signer">Signing clinician</Label>
                    <Input id="signer" value={signer} onChange={(event) => setSigner(event.target.value)} placeholder="Full name" />
                  </div>
                  <Button onClick={sign} disabled={!signer.trim() || signing}>
                    {signing ? "Signing…" : "Sign & approve"}
                  </Button>
                </div>
              )}
            </Card>
          </div>
        ) : null}
      </DataState>
    </div>
  );
}

export default function DoctorReportViewerPage() {
  const params = useParams<{ code: string }>();
  const code = Array.isArray(params.code) ? params.code[0] : params.code;
  return (
    <WorkspaceScreen title="Result viewer" workspacePath="/app/doctor" permission="portal.doctor.read">
      {(ctx) => <ReportPanel {...ctx} reportCode={code ?? ""} />}
    </WorkspaceScreen>
  );
}
