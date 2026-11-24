import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { LandingNav } from "./LandingNav";
import { LandingFooter } from "./LandingFooter";
import { LANDING, type Lang } from "@/lib/landing/i18n";

export function AboutPage({ lang }: { lang: Lang }) {
  const t = LANDING[lang].about;
  return (
    <div lang={lang} className="min-h-screen bg-slate-950">
      <LandingNav lang={lang} path="/about" />
      <main>
        <section className="relative overflow-hidden px-4 pb-16 pt-16 lg:px-8 lg:pt-24">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(20,184,166,0.25),transparent_45%)]" />
          <div className="relative mx-auto max-w-4xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-teal-300">{t.eyebrow}</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-white sm:text-5xl">{t.title}</h1>
            <p className="mt-6 text-lg text-slate-300">{t.lead}</p>
          </div>
        </section>

        <section className="bg-white px-4 py-16 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <h2 className="text-3xl font-semibold text-slate-900">{t.roleTitle}</h2>
            <div className="mt-8 grid gap-5 md:grid-cols-2">
              {t.roles.map(([title, text]) => (
                <div key={title} className="rounded-2xl border border-slate-200 p-6">
                  <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
                  <p className="mt-2 text-slate-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-50 px-4 py-16 lg:px-8">
          <div className="mx-auto max-w-7xl">
            <h2 className="text-3xl font-semibold text-slate-900">{t.whyTitle}</h2>
            <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {t.why.map(([title, text]) => (
                <div key={title} className="rounded-2xl border border-teal-100 bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-teal-800">{title}</h3>
                  <p className="mt-2 text-sm text-slate-600">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="bg-slate-900 px-4 py-16 text-white lg:px-8">
          <div className="mx-auto max-w-7xl">
            <h2 className="text-3xl font-semibold">{t.flowTitle}</h2>
            <ol className="mt-8 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {t.flow.map((step, i) => (
                <li key={step} className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <span className="text-xs font-semibold text-teal-300">{i + 1}</span>
                  <p className="mt-1 text-sm font-medium">{step}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="bg-white px-4 py-16 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-semibold text-slate-900">{t.ctaTitle}</h2>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Link
                href={`/${lang}#contact`}
                className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-5 py-3 text-sm font-medium text-white hover:bg-teal-700"
              >
                {t.ctaDemo}
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/book"
                className="inline-flex items-center rounded-lg border border-teal-600 px-5 py-3 text-sm font-medium text-teal-700 hover:bg-teal-50"
              >
                {t.ctaBook}
              </Link>
            </div>
          </div>
        </section>
      </main>
      <LandingFooter lang={lang} />
    </div>
  );
}
