// utils.ts:pure helpers only. No DOM, no side effects.

/** Join class names, dropping falsy values. */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}

/** Join non-empty parts with the " · " separator used across name/meta lines. */
export function joinDots(...parts: Array<string | number | null | undefined | false>): string {
  return parts.filter(Boolean).join(' · ');
}

/** THE numeric-count rendering: grouped digits in the app's English locale,
    pinned so the same number can never format two ways in one screen. */
export function formatCount(n: number): string {
  return n.toLocaleString('en');
}

/** The English count noun, e.g. pluralNoun(1, 'work') = "work",
    pluralNoun(2, 'category', 'categories') = "categories". The one place the
    n-equals-1 rule lives, so "1 works" can't appear anywhere. */
export function pluralNoun(n: number, singular: string, plural = `${singular}s`): string {
  return n === 1 ? singular : plural;
}

/** The one grammar for a counted noun, e.g. "1,204 works". */
export function countLabel(n: number, singular: string, plural?: string): string {
  return `${formatCount(n)} ${pluralNoun(n, singular, plural)}`;
}

/** English death-year label for a meta badge, e.g. "d. 326 AH"; empty when
    the year is unknown. The upstream 99999 sentinel never reaches the client:
    the catalog build normalizes it to null and the served model bounds the
    field, so null is the only absent form. */
export function deathLabel(ah?: number | null): string {
  if (ah == null) return '';
  return `d. ${ah} AH`;
}

/** Volume-count fragment for a work's meta line: "" for a single volume
    (stating "1 vols" would be noise), else e.g. "3 vols". */
export function volumesLabel(volumeCount: number): string {
  return volumeCount > 1 ? countLabel(volumeCount, 'vol') : '';
}

/** Clamp a number into [min, max]. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/** Number of pages for ``total`` items at ``perPage`` each (at least 1). */
export function pageCount(total: number, perPage: number): number {
  return Math.max(1, Math.ceil(total / perPage));
}

/** Inclusive 1-based page window for pagination, capped at `size` entries. */
export function pageWindow(current: number, total: number, size: number): number[] {
  const half = Math.floor(size / 2);
  let start = Math.max(1, current - half);
  const end = Math.min(total, start + size - 1);
  start = Math.max(1, end - size + 1);
  const out: number[] = [];
  for (let p = start; p <= end; p += 1) out.push(p);
  return out;
}

/** Render Western digits in a number/string as Arabic-Indic digits. */
const ARABIC_DIGITS = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
export function toArabicDigits(value: number | string): string {
  return String(value).replace(/[0-9]/g, (d) => ARABIC_DIGITS[Number(d)] ?? d);
}

/** URL-safe base64 (RFC 4648 §5) of a UTF-8 string: compacts free text bound
    for a URL param. Plain percent-encoding roughly triples non-ASCII text —
    every UTF-8 byte becomes 3 characters — which is punishing for Arabic,
    where each base letter AND each combining diacritic is its own escaped
    byte; base64 costs only ~4/3 of the raw byte count. Used by routes.ts for
    the reader/search query and the active-book filter, the only free-text
    URL fields. */
export function toBase64Url(value: string): string {
  const bytes = new TextEncoder().encode(value);
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** The inverse of toBase64Url. Never throws: a hand-edited or truncated URL
    decodes to '' instead of crashing the router. */
export function fromBase64Url(value: string): string {
  if (!value) return '';
  const padded = value.replace(/-/g, '+').replace(/_/g, '/');
  const pad = padded.length % 4 === 0 ? '' : '='.repeat(4 - (padded.length % 4));
  try {
    const binary = atob(padded + pad);
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  } catch {
    return '';
  }
}
