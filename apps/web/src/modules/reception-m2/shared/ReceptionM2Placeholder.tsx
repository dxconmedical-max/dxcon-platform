"use client";

/**
 * Shared M2 architecture placeholder shell.
 * Not a product feature — indicates foundation without business logic.
 */
export function ReceptionM2Placeholder({
  title,
  domain,
  description,
}: {
  title: string;
  domain: string;
  description: string;
}) {
  return (
    <div className="mx-auto max-w-2xl space-y-4 py-8">
      <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
        Reception M2 · Architecture foundation
      </p>
      <h1 className="text-2xl font-semibold text-neutral-900">{title}</h1>
      <p className="text-sm text-neutral-600">{description}</p>
      <div className="rounded-lg border border-dashed border-neutral-300 bg-neutral-50 p-4 text-sm text-neutral-700">
        <p>
          Domain module: <code className="font-mono text-xs">modules/reception-m2/{domain}</code>
        </p>
        <p className="mt-2">
          Business logic is not implemented on this page. Canonical API client remains{" "}
          <code className="font-mono text-xs">@/lib/api/reception</code>.
        </p>
      </div>
    </div>
  );
}
