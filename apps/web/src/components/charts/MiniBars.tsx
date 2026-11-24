/** Dependency-free bar chart. Values are always shown as text under each bar, never colour alone. */
export function MiniBars({
  points,
  format,
  label,
}: {
  points: { label: string; value: number }[];
  format?: (value: number) => string;
  label: string;
}) {
  const max = Math.max(1, ...points.map((p) => p.value));
  return (
    <div role="img" aria-label={label} className="flex h-44 items-end gap-1.5 overflow-x-auto">
      {points.map((p) => (
        <div key={p.label} className="flex min-w-8 flex-1 flex-col items-center justify-end gap-1">
          <span className="text-[10px] text-slate-500">{format ? format(p.value) : p.value}</span>
          <div
            className="w-full rounded-t bg-teal-600"
            style={{ height: `${Math.max(2, (p.value / max) * 100)}px` }}
          />
          <span className="text-[10px] text-slate-500">{p.label}</span>
        </div>
      ))}
    </div>
  );
}
