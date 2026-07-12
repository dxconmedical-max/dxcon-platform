"use client";

import { useRef, useState } from "react";
import { Camera } from "lucide-react";

import { WorkspaceScreen, type WorkspaceContext } from "@/components/layout/WorkspaceScreen";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import {
  DataState,
  ScannerPlaceholder,
  SectionHeader,
  SimpleTable,
  StatusPill,
} from "@/components/workspace/primitives";
import { useSourcedData } from "@/hooks/useSourcedData";
import {
  fetchCollectionJobs,
  uploadSpecimenPhoto,
  type CollectionJob,
} from "@/lib/api/collector";

function JobsPanel({ accessToken, organizationId, userId }: WorkspaceContext) {
  const state = useSourcedData<CollectionJob[]>(
    () => fetchCollectionJobs({ token: accessToken, organizationId, collectorId: userId }),
    [accessToken, organizationId, userId],
  );
  const rows = state.data ?? [];

  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [uploadMsg, setUploadMsg] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  function onSelectFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      setUploading(true);
      setUploadMsg(null);
      void uploadSpecimenPhoto(
        { token: accessToken, organizationId },
        {
          assignmentId: activeJob ?? "unassigned",
          fileName: file.name,
          contentBase64: base64,
        },
      )
        .then((res) => setUploadMsg(res.value.message))
        .catch(() => setUploadMsg("Upload failed. Try again."))
        .finally(() => setUploading(false));
    };
    reader.readAsDataURL(file);
  }

  return (
    <div className="space-y-4">
      <SectionHeader
        title="Assigned collections"
        description="Today's collection assignments."
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
        emptyLabel="No assigned collection jobs."
        onRetry={state.reload}
      >
        <SimpleTable<CollectionJob>
          rows={rows}
          rowKey={(row) => row.assignment_id}
          columns={[
            { key: "time", label: "Time", render: (r) => r.scheduled_at ?? "—" },
            { key: "patient", label: "Patient", render: (r) => r.patient_name },
            { key: "address", label: "Address", render: (r) => r.address ?? "—" },
            { key: "service", label: "Service", render: (r) => r.service ?? "—" },
            {
              key: "priority",
              label: "Priority",
              render: (r) =>
                r.priority ? (
                  <Badge className={r.priority === "URGENT" ? "bg-rose-100 text-rose-700" : ""}>{r.priority}</Badge>
                ) : (
                  "—"
                ),
            },
            { key: "status", label: "Status", render: (r) => <StatusPill status={r.status} /> },
            {
              key: "action",
              label: "",
              render: (r) => (
                <Button
                  size="sm"
                  variant={activeJob === r.assignment_id ? "primary" : "outline"}
                  onClick={() => setActiveJob(r.assignment_id)}
                >
                  {activeJob === r.assignment_id ? "Selected" : "Select"}
                </Button>
              ),
            },
          ]}
        />
      </DataState>

      <div className="grid gap-4 md:grid-cols-2">
        <ScannerPlaceholder
          label="Scan specimen barcode"
          onSimulate={() => setUploadMsg(`Scanned barcode for ${activeJob ?? "selected job"}.`)}
        />
        <Card className="flex flex-col items-center justify-center gap-3 border-dashed py-8 text-center">
          <Camera className="h-8 w-8 text-teal-600" />
          <div>
            <p className="text-sm font-medium text-slate-800">Upload specimen photo</p>
            <p className="mt-1 text-xs text-slate-500">
              {activeJob ? `For job ${activeJob}` : "Select a job first"}
            </p>
          </div>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(event) => {
              const file = event.target.files?.[0];
              if (file) onSelectFile(file);
              event.target.value = "";
            }}
          />
          <Button
            size="sm"
            variant="outline"
            disabled={!activeJob || uploading}
            onClick={() => fileRef.current?.click()}
          >
            {uploading ? "Uploading…" : "Choose photo"}
          </Button>
          {uploadMsg ? <p className="text-xs text-slate-500">{uploadMsg}</p> : null}
        </Card>
      </div>
    </div>
  );
}

export default function CollectorJobsPage() {
  return (
    <WorkspaceScreen title="Assigned jobs" workspacePath="/app/collector" permission="collections.read">
      {(ctx) => <JobsPanel {...ctx} />}
    </WorkspaceScreen>
  );
}
