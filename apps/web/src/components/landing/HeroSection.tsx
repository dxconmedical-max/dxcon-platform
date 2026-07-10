import Link from "next/link";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

export function HeroSection() {
  return (
    <section className="relative overflow-hidden px-4 pb-20 pt-16 lg:px-8 lg:pb-28 lg:pt-24">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(20,184,166,0.25),transparent_45%),radial-gradient(circle_at_bottom_left,rgba(37,99,235,0.18),transparent_40%)]" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 lg:grid-cols-2">
        <div>
          <Badge tone="info" className="bg-teal-500/10 text-teal-200">
            Healthcare diagnostics platform
          </Badge>
          <h1 className="mt-5 text-4xl font-semibold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Connect labs, clinics, and patients on one trusted platform
          </h1>
          <p className="mt-6 max-w-xl text-lg text-slate-300">
            DxCon unifies orders, home collection, lab operations, and clinical
            reporting with enterprise-grade security and AI-assisted insights.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/login">
              <Button size="lg">
                Sign in
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <a href="#contact">
              <Button size="lg" variant="outline" className="border-slate-600 text-white hover:border-teal-400">
                Contact sales
              </Button>
            </a>
          </div>
          <div className="mt-10 flex flex-wrap gap-6 text-sm text-slate-300">
            <span className="inline-flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-teal-400" />
              HIPAA-ready architecture
            </span>
            <span className="inline-flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-teal-400" />
              AI clinical insights
            </span>
          </div>
        </div>
        <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl shadow-teal-900/20 backdrop-blur">
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              ["Orders today", "1,248"],
              ["Avg. TAT", "4.2h"],
              ["Active partners", "86"],
              ["Home collections", "312"],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-2xl border border-white/10 bg-slate-900/60 p-4"
              >
                <p className="text-xs uppercase tracking-wide text-slate-400">
                  {label}
                </p>
                <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm text-slate-400">
            Live metrics powered by the DxCon production API.
          </p>
        </div>
      </div>
    </section>
  );
}
