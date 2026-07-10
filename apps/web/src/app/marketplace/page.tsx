import Link from "next/link";

export const metadata = { title: "Marketplace" };

export default function MarketplacePage() {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white px-4 py-4">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Link href="/" className="text-lg font-semibold text-teal-700">DxCon Marketplace</Link>
          <nav className="flex gap-4 text-sm">
            <Link href="/marketplace/tests">Tests</Link>
            <Link href="/marketplace/packages">Packages</Link>
            <Link href="/marketplace/providers">Providers</Link>
            <Link href="/app/patient/bookings">My bookings</Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-slate-900">Discover healthcare services</h1>
        <p className="mt-2 text-slate-600">Search, compare and book lab tests, consultations and home collection.</p>
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { href: "/marketplace/tests", label: "Lab tests", desc: "Search by test name or code" },
            { href: "/marketplace/packages", label: "Health packages", desc: "Bundled check-up packages" },
            { href: "/marketplace/providers", label: "Providers", desc: "Labs, clinics and hospitals" },
            { href: "/marketplace/compare", label: "Compare", desc: "Compare up to 4 options" },
            { href: "/marketplace/book", label: "Book", desc: "Start a new booking" },
          ].map((item) => (
            <Link key={item.href} href={item.href} className="rounded-xl border bg-white p-5 shadow-sm hover:border-teal-300">
              <h2 className="font-semibold text-slate-900">{item.label}</h2>
              <p className="mt-1 text-sm text-slate-600">{item.desc}</p>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
