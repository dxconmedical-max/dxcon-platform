import Link from "next/link";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";

export const metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <MarketingPageShell>
      <article className="mx-auto max-w-3xl px-4 py-20 text-slate-300 lg:px-8">
        <Link href="/" className="text-sm text-teal-400 hover:text-teal-300">
          ← Back to home
        </Link>
        <h1 className="mt-6 text-3xl font-semibold text-white">Privacy policy</h1>
        <p className="mt-4 text-sm leading-relaxed text-slate-400">
          DxCon processes healthcare operational data under organization-controlled
          agreements. This pilot site does not collect personal data through marketing
          forms beyond what you submit via email to our sales team. Authenticated
          workspaces enforce role-based access, audit logging, and tenant isolation
          as described in your organization&apos;s service terms.
        </p>
        <p className="mt-4 text-sm leading-relaxed text-slate-400">
          For privacy inquiries contact{" "}
          <a href="mailto:privacy@dxcon.com.vn" className="text-teal-400 hover:text-teal-300">
            privacy@dxcon.com.vn
          </a>
          .
        </p>
      </article>
    </MarketingPageShell>
  );
}
