import { en, type MessageTree } from "./locales/en";
import { vi } from "./locales/vi";

export type Locale = "en" | "vi";

const catalogs: Record<Locale, MessageTree> = { en, vi };

/** Default locale until user preference or Accept-Language routing is added. */
export const DEFAULT_LOCALE: Locale = "en";

function resolvePath(tree: Record<string, unknown>, key: string): string | undefined {
  const parts = key.split(".");
  let current: unknown = tree;
  for (const part of parts) {
    if (!current || typeof current !== "object" || !(part in current)) {
      return undefined;
    }
    current = (current as Record<string, unknown>)[part];
  }
  return typeof current === "string" ? current : undefined;
}

export function t(key: string, locale: Locale = DEFAULT_LOCALE): string {
  return resolvePath(catalogs[locale] as unknown as Record<string, unknown>, key) ?? key;
}

export function getMessages(locale: Locale = DEFAULT_LOCALE): MessageTree {
  return catalogs[locale];
}
