import Link from "next/link";

export default function SessionExpiredPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center">
        <h1 className="text-3xl font-semibold">Session expired</h1>
        <p className="mt-2 text-slate-600">Please sign in again to continue.</p>
        <Link href="/login?reason=session-expired" className="mt-6 inline-block text-teal-700">
          Sign in
        </Link>
      </div>
    </div>
  );
}
