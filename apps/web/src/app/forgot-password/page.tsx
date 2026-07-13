import Link from "next/link";

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm text-center">
        <h1 className="text-2xl font-semibold">Forgot password</h1>
        <p className="mt-3 text-sm text-slate-600">
          Self-service password reset is not yet enabled. Outbound email (SMTP) must be
          configured before reset links can be delivered.
        </p>
        <p className="mt-2 text-xs text-slate-500">
          Contact your organization administrator to restore access.
        </p>
        <Link href="/login" className="mt-6 inline-block text-teal-700 text-sm">
          Return to sign in
        </Link>
      </div>
    </div>
  );
}
