import Link from "next/link";

export default function ForbiddenPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center">
        <h1 className="text-3xl font-semibold text-slate-900">Access denied</h1>
        <p className="mt-2 text-slate-600">You do not have permission to view this page.</p>
        <Link href="/app" className="mt-6 inline-block text-teal-700">
          Go to workspace
        </Link>
      </div>
    </div>
  );
}
