"use client";

import { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import {
  CONSENT_TYPES,
  getPatientConsents,
  recordPatientConsents,
  type ConsentType,
  type PatientConsents,
} from "@/lib/api/receptionConsent";

const LABELS: Record<ConsentType, string> = {
  LAB_TEST: "Testing (required) — Xét nghiệm",
  PARTNER_LAB: "Partner laboratories — Phòng xét nghiệm đối tác",
  CLINIC_SHARE: "Share results with referring clinic — Chia sẻ kết quả với phòng khám",
  CONTACT: "Contact by phone or SMS — Liên hệ",
  OVERSEAS_STORAGE: "Storage and processing abroad (Singapore) — Lưu trữ ở nước ngoài",
};

type Props = {
  accessToken: string;
  organizationId?: string | null;
  patientCode: string;
};

function emptyChecks(): Record<ConsentType, boolean> {
  return {
    LAB_TEST: false,
    PARTNER_LAB: false,
    CLINIC_SHARE: false,
    CONTACT: false,
    OVERSEAS_STORAGE: false,
  };
}

export function ConsentPanel({ accessToken, organizationId, patientCode }: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<PatientConsents | null>(null);
  const [checks, setChecks] = useState<Record<ConsentType, boolean>>(emptyChecks);
  const [method, setMethod] = useState<"PAPER" | "ELECTRONIC">("PAPER");
  const [documentRef, setDocumentRef] = useState("");
  const [hasGuardian, setHasGuardian] = useState(false);
  const [guardian, setGuardian] = useState({ name: "", relationship: "", document: "" });

  const ctx = { token: accessToken, organizationId };

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getPatientConsents(
        { token: accessToken, organizationId },
        patientCode,
      );
      setSaved(result);
      const next = emptyChecks();
      for (const type of CONSENT_TYPES) {
        next[type] = Boolean(result.consents?.[type]?.granted);
      }
      setChecks(next);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }, [accessToken, organizationId, patientCode]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      const result = await recordPatientConsents(ctx, patientCode, {
        consents: CONSENT_TYPES.map((type) => ({ consent_type: type, granted: checks[type] })),
        method,
        document_ref: documentRef.trim() || undefined,
        guardian: hasGuardian ? guardian : undefined,
      });
      setSaved(result);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setSaving(false);
    }
  }

  const labTestGranted = Boolean(saved?.consents?.LAB_TEST?.granted);

  return (
    <section
      className="space-y-3 rounded-xl border border-slate-200 bg-white p-4"
      aria-label="Patient consent"
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-slate-900">Patient consent</h3>
        {loading ? (
          <span className="text-xs text-slate-500">Loading…</span>
        ) : labTestGranted ? (
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
            Testing consent recorded
          </span>
        ) : (
          <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
            Testing consent not recorded
          </span>
        )}
      </div>

      <p className="text-xs text-slate-500">
        Tick only what the patient agreed to on the signed form. Boxes start empty on purpose. Wording
        follows the lawyer-reviewed consent form.
      </p>

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-2 text-sm text-rose-700">
          {error}
        </div>
      ) : null}

      <ul className="space-y-2">
        {CONSENT_TYPES.map((type) => (
          <li key={type}>
            <label className="flex items-start gap-2 text-sm text-slate-800">
              <input
                type="checkbox"
                className="mt-0.5"
                checked={checks[type]}
                disabled={loading || saving}
                onChange={(event) => setChecks((prev) => ({ ...prev, [type]: event.target.checked }))}
              />
              <span>{LABELS[type]}</span>
            </label>
          </li>
        ))}
      </ul>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <Label htmlFor="consent-method">How was consent given</Label>
          <select
            id="consent-method"
            className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm"
            value={method}
            onChange={(event) => setMethod(event.target.value as "PAPER" | "ELECTRONIC")}
            disabled={saving}
          >
            <option value="PAPER">Paper form (Phiếu giấy)</option>
            <option value="ELECTRONIC">Electronic (Điện tử)</option>
          </select>
        </div>
        <div>
          <Label htmlFor="consent-doc">Form reference (optional)</Label>
          <Input
            id="consent-doc"
            value={documentRef}
            maxLength={100}
            onChange={(event) => setDocumentRef(event.target.value)}
            disabled={saving}
          />
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-800">
        <input
          type="checkbox"
          checked={hasGuardian}
          onChange={(event) => setHasGuardian(event.target.checked)}
          disabled={saving}
        />
        <span>Signed by a legal representative (minor or cannot decide) — Người đại diện ký</span>
      </label>

      {hasGuardian ? (
        <div className="grid gap-3 sm:grid-cols-3">
          <div>
            <Label htmlFor="guardian-name">Full name</Label>
            <Input
              id="guardian-name"
              value={guardian.name}
              onChange={(event) => setGuardian((prev) => ({ ...prev, name: event.target.value }))}
            />
          </div>
          <div>
            <Label htmlFor="guardian-rel">Relationship</Label>
            <Input
              id="guardian-rel"
              value={guardian.relationship}
              onChange={(event) =>
                setGuardian((prev) => ({ ...prev, relationship: event.target.value }))
              }
            />
          </div>
          <div>
            <Label htmlFor="guardian-doc">Supporting document</Label>
            <Input
              id="guardian-doc"
              value={guardian.document}
              onChange={(event) => setGuardian((prev) => ({ ...prev, document: event.target.value }))}
            />
          </div>
        </div>
      ) : null}

      <div className="flex justify-end">
        <Button size="sm" onClick={() => void save()} disabled={loading || saving}>
          {saving ? "Saving…" : "Save consent"}
        </Button>
      </div>
    </section>
  );
}
