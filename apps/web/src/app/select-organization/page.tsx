"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";

export default function SelectOrganizationPage() {
  const router = useRouter();
  const { memberships, selectOrganization, isBootstrapping } = useAuth();

  if (isBootstrapping) {
    return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <h1 className="text-2xl font-semibold">Select organization</h1>
        <p className="mt-2 text-sm text-slate-600">
          Choose the organization you want to work in.
        </p>
        <ul className="mt-6 space-y-3">
          {memberships.map((m) => (
            <li key={m.organization_id}>
              <Button
                variant="outline"
                className="w-full justify-start"
                disabled={m.membership_status !== "active"}
                onClick={() =>
                  void selectOrganization(m.organization_id).then((path) =>
                    router.push(path),
                  )
                }
              >
                <span className="text-left">
                  <span className="block font-medium">{m.organization_name}</span>
                  <span className="block text-xs text-slate-500">
                    {m.organization_type} · {m.membership_status}
                  </span>
                </span>
              </Button>
            </li>
          ))}
        </ul>
        <p className="mt-4 text-center text-sm">
          <Link href="/logout" className="text-teal-700">Sign out</Link>
        </p>
      </div>
    </div>
  );
}
