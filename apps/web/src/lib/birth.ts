export type BirthInput = { year: number; date: string | null };

/**
 * Accepts "dd/mm/yyyy", "d/m/yyyy" or just "yyyy". A bare year is kept as year only,
 * so nobody invents a day and month. Returns an error message in Vietnamese on bad input.
 */
export function parseBirthInput(raw: string, now: Date = new Date()): { value?: BirthInput; error?: string } {
  const text = raw.trim();
  const thisYear = now.getFullYear();
  if (/^\d{4}$/.test(text)) {
    const year = Number(text);
    if (year < 1900 || year > thisYear) return { error: "Năm sinh chưa đúng." };
    return { value: { year, date: null } };
  }
  const m = text.match(/^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})$/);
  if (!m) return { error: "Nhập ngày sinh dạng dd/mm/yyyy, hoặc chỉ nhập năm (ví dụ 1985)." };
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  const d = new Date(year, month - 1, day);
  if (d.getFullYear() !== year || d.getMonth() !== month - 1 || d.getDate() !== day) {
    return { error: "Ngày sinh không tồn tại." };
  }
  if (year < 1900 || d > now) return { error: "Ngày sinh chưa đúng." };
  const iso = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
  return { value: { year, date: iso } };
}

/** Show the full date when known, otherwise only the year. */
export function formatBirth(date: string | null | undefined, year?: number | null): string {
  if (date && /^\d{4}-\d{2}-\d{2}$/.test(date)) {
    const [y, m, d] = date.split("-");
    return `${d}/${m}/${y}`;
  }
  if (date && /^\d{4}$/.test(date)) return date;
  return year ? String(year) : "—";
}
