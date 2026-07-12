import Link from "next/link";
import type { ReactNode } from "react";

export function MarketplacePublicShell({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b bg-white px-4 py-4">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3">
          <Link href="/" className="text-lg font-semibold text-teal-700">
            DxCon
          </Link>
          <nav className="flex flex-wrap gap-4 text-sm text-slate-600">
            <Link href="/services" className="hover:text-teal-700">
              Services
            </Link>
            <Link href="/packages" className="hover:text-teal-700">
              Packages
            </Link>
            <Link href="/partners" className="hover:text-teal-700">
              Partners
            </Link>
            <Link href="/app/patient/book" className="font-medium text-teal-700">
              Book now
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <h1 className="text-2xl font-bold text-slate-900">{title}</h1>
        <div className="mt-6">{children}</div>
      </main>
      <footer className="mt-12 border-t bg-white px-4 py-8 text-sm text-slate-500">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <p>© {new Date().getFullYear()} DxCon Medical</p>
          <div className="flex flex-wrap gap-4">
            <Link href="/privacy" className="hover:text-teal-700">
              Privacy
            </Link>
            <Link href="/terms" className="hover:text-teal-700">
              Terms
            </Link>
            <Link href="/contact" className="hover:text-teal-700">
              Contact
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
