import Link from "next/link";

export const metadata = { title: "Providers" };

export default function MarketplaceProvidersPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <h1 className="text-xl font-bold">Providers</h1>
      <p className="mt-2 text-sm text-slate-600">
        <Link href="/marketplace/providers/demo" className="text-teal-700">View sample provider profile</Link>
      </p>
    </div>
  );
}
