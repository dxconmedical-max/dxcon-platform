"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { verifyReportToken } from "@/lib/api/clinical";

export default function VerifyReportPage() {
  const params = useParams();
  const token = String(params.token ?? "");
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    verifyReportToken(token)
      .then(setResult)
      .catch(() => setError("Verification unavailable"));
  }, [token]);

  return (
    <main className="mx-auto max-w-lg p-8">
      <h1 className="text-xl font-semibold">Report verification</h1>
      <p className="mt-2 text-sm text-slate-600">
        Authenticity check only. Full clinical content is available to authorized users via secure portal access.
      </p>
      {error && <p className="mt-4 text-red-600">{error}</p>}
      {result && (
        <div className="mt-4 rounded border p-4 text-sm">
          <p>Valid: {String(result.valid ?? false)}</p>
          {result.report_code ? <p>Report code: {String(result.report_code)}</p> : null}
          {result.report_version != null ? <p>Version: {String(result.report_version)}</p> : null}
          {result.report_status ? <p>Status: {String(result.report_status)}</p> : null}
          {result.message ? <p className="mt-2 text-slate-500">{String(result.message)}</p> : null}
        </div>
      )}
    </main>
  );
}
