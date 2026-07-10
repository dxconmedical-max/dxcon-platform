import Link from "next/link";
import { Activity } from "lucide-react";

import { Button } from "@/components/ui/Button";

export function LandingNav() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/10 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-teal-500">
            <Activity className="h-5 w-5" />
          </span>
          <span className="text-lg font-semibold">DxCon</span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm text-slate-300 md:flex">
          <a href="#services" className="hover:text-white">
            Services
          </a>
          <a href="#ai" className="hover:text-white">
            AI
          </a>
          <a href="#partners" className="hover:text-white">
            Partners
          </a>
          <a href="#pricing" className="hover:text-white">
            Pricing
          </a>
          <a href="#contact" className="hover:text-white">
            Contact
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <Link href="/login">
            <Button variant="ghost" className="text-slate-200 hover:bg-white/10 hover:text-white">
              Sign in
            </Button>
          </Link>
          <a href="#contact">
            <Button>Book demo</Button>
          </a>
        </div>
      </div>
    </header>
  );
}
