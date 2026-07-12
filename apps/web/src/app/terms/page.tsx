import Link from "next/link";

import { MarketingPageShell } from "@/components/landing/MarketingPageShell";

export const metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <MarketingPageShell>
      <article className="mx-auto max-w-3xl px-4 py-20 text-slate-300 lg:px-8">
        <Link href="/" className="text-sm text-teal-400 hover:text-teal-300">
          ← Back to home
        </Link>
        <h1 className="mt-6 text-3xl font-semibold text-white">Terms of use</h1>
        <p className="mt-4 text-sm leading-relaxed text-slate-400">
          Access to DxCon production workspaces requires an authorized account issued
          by your organization administrator. Marketing content on this site is for
          informational purposes and does not constitute a medical device clearance,
          compliance certification, or service level commitment unless executed under
          a signed agreement.
        </p>
        <p className="mt-4 text-sm leading-relaxed text-slate-400">
          AI-assisted features provide advisory output subject to human review and
          must not be used as the sole basis for clinical decisions.
        </p>
      </article>
    </MarketingPageShell>
  );
}
