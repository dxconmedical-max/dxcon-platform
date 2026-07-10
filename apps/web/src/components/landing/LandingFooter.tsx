import Link from "next/link";

export function LandingFooter() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 px-4 py-10 text-slate-400 lg:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 md:flex-row md:items-center md:justify-between">
        <div>
          <p className="text-white font-semibold">DxCon</p>
          <p className="mt-1 text-sm">Connected diagnostics for modern healthcare.</p>
        </div>
        <div className="flex flex-wrap gap-4 text-sm">
          <Link href="/login" className="hover:text-white">
            Sign in
          </Link>
          <a href="#pricing" className="hover:text-white">
            Pricing
          </a>
          <a href="#contact" className="hover:text-white">
            Contact
          </a>
        </div>
        <p className="text-xs">© {new Date().getFullYear()} DxCon Medical</p>
      </div>
    </footer>
  );
}
