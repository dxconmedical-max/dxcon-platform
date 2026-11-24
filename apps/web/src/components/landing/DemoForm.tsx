"use client";

import { FormEvent, useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { normalizeApiError } from "@/lib/errors";
import { submitDemoRequest } from "@/lib/api/publicDemo";
import { LANDING, type Lang } from "@/lib/landing/i18n";

export function DemoForm({ lang }: { lang: Lang }) {
  const t = LANDING[lang].contact;
  const [name, setName] = useState("");
  const [org, setOrg] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [consent, setConsent] = useState(false);
  const [website, setWebsite] = useState(""); // honeypot
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reference, setReference] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await submitDemoRequest({
        full_name: name.trim(),
        organization: org.trim() || undefined,
        email: email.trim(),
        phone: phone.trim() || undefined,
        message: message.trim() || undefined,
        lang,
        consent_contact: consent,
        website,
      });
      setReference(result.reference);
    } catch (err) {
      setError(normalizeApiError(err));
    } finally {
      setLoading(false);
    }
  }

  if (reference) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-xl font-semibold text-slate-900">{t.doneTitle}</h3>
        <p className="mt-3 text-sm text-slate-600">{t.doneText}</p>
        <p className="mt-3 text-lg font-semibold text-teal-700">{reference}</p>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="name">{t.name} *</Label>
          <Input id="name" name="name" required maxLength={120} placeholder={t.namePh} value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="organization">{t.org}</Label>
          <Input id="organization" name="organization" maxLength={160} placeholder={t.orgPh} value={org} onChange={(e) => setOrg(e.target.value)} />
        </div>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <div>
          <Label htmlFor="email">{t.email} *</Label>
          <Input id="email" name="email" type="email" required maxLength={120} placeholder="you@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <Label htmlFor="phone">{t.phone}</Label>
          <Input id="phone" name="phone" type="tel" inputMode="tel" placeholder="0901234567" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </div>
      </div>
      <div className="mt-4">
        <Label htmlFor="message">{t.message}</Label>
        <textarea
          id="message"
          name="message"
          rows={4}
          maxLength={1000}
          placeholder={t.messagePh}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-500/20"
        />
      </div>
      {/* Honeypot: hidden from people, bots fill it. */}
      <div aria-hidden="true" style={{ position: "absolute", left: "-9999px", height: 0, overflow: "hidden" }}>
        <label>
          Website
          <input tabIndex={-1} autoComplete="off" value={website} onChange={(e) => setWebsite(e.target.value)} />
        </label>
      </div>
      <label className="mt-4 flex items-start gap-2 text-sm text-slate-600">
        <input type="checkbox" className="mt-1" checked={consent} onChange={(e) => setConsent(e.target.checked)} required />
        <span>{t.consent}</span>
      </label>
      {error ? <p role="alert" className="mt-3 text-sm text-red-600">{error}</p> : null}
      <Button type="submit" disabled={loading} className="mt-6 w-full">
        {loading ? t.sending : t.send}
      </Button>
    </form>
  );
}
