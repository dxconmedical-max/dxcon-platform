import type { ReactNode } from "react";

import { LandingFooter } from "@/components/landing/LandingFooter";
import { LandingNav } from "@/components/landing/LandingNav";
import { isPlaceholder } from "@/lib/site";

/** Hiển thị giá trị pháp nhân; chỗ trống được tô vàng để dễ nhận ra. */
export function Fill({ value }: { value: string }) {
  return isPlaceholder(value) ? (
    <mark className="rounded bg-amber-200 px-1 text-amber-900">{value}</mark>
  ) : (
    <>{value}</>
  );
}

export function LegalPage({
  title,
  updated,
  children,
}: {
  title: string;
  updated?: string;
  children: ReactNode;
}) {
  return (
    <div className="min-h-screen bg-white">
      <LandingNav lang="vi" />
      <main className="mx-auto max-w-3xl px-4 py-12 lg:px-8">
        <h1 className="text-3xl font-semibold text-slate-900">{title}</h1>
        {updated ? <p className="mt-2 text-sm text-slate-500">Cập nhật lần cuối: {updated}</p> : null}
        <div className="mt-8 space-y-4 text-[15px] leading-7 text-slate-700 [&_h2]:mt-8 [&_h2]:text-xl [&_h2]:font-semibold [&_h2]:text-slate-900 [&_ul]:list-disc [&_ul]:space-y-1 [&_ul]:pl-6 [&_a]:text-teal-700 [&_a]:underline">
          {children}
        </div>
      </main>
      <LandingFooter lang="vi" />
    </div>
  );
}
