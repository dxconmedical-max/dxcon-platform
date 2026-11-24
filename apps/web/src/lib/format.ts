export function formatVnd(value: number): string {
  return new Intl.NumberFormat("vi-VN").format(Math.round(value)) + " ₫";
}

export function shortDate(iso: string): string {
  const [, m, d] = iso.split("-");
  return d && m ? `${d}/${m}` : iso;
}
