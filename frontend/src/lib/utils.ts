// utils.ts:pure helpers only. No DOM, no side effects.

import { BOOK } from './constants';

/** Join class names, dropping falsy values. */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ');
}

/** Join non-empty parts with the " · " separator used across name/meta lines. */
export function joinDots(...parts: Array<string | number | null | undefined | false>): string {
  return parts.filter(Boolean).join(' · ');
}

/** English death-year label for a meta badge, e.g. "d. 326 AH"; empty when the
    year is missing or is the unknown-year sentinel. */
export function deathLabel(ah?: number | null): string {
  if (ah == null || ah === BOOK.UNKNOWN_DEATH_YEAR) return '';
  return `d. ${ah} AH`;
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
  return String(value).replace(/[0-9]/g, (d) => ARABIC_DIGITS[Number(d)]);
}
