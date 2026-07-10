import Link from "next/link";

export default function ServiceUnavailablePage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <div className="text-center">
        <h1 className="text-3xl font-semibold">Service unavailable</h1>
        <p className="mt-2 text-slate-600">
          DxCon API is temporarily unreachable. Please try again shortly.
        </p>
        <Link href="/" className="mt-6 inline-block text-teal-700">
          Return home
        </Link>
      </div>
    </div>
  );
}
