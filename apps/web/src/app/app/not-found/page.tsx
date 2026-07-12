import Link from "next/link";

import { Button } from "@/components/ui/Button";

export const metadata = { title: "Not found" };

export default function AppNotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <h1 className="text-2xl font-semibold text-slate-900">Page not found</h1>
      <p className="mt-2 text-sm text-slate-600">
        This workspace route does not exist or you may not have access.
      </p>
      <div className="mt-6 flex gap-3">
        <Link href="/app">
          <Button>Go to workspace</Button>
        </Link>
        <Link href="/login">
          <Button variant="outline">Sign in</Button>
        </Link>
      </div>
    </div>
  );
}
