// utils.ts — pure helpers only. No DOM, no side effects.
// Stage-1 reconciliation: dropped the orphaned `gradeTone` helper and its
// `GRADE_TONE` import — that symbol no longer exists in constants.ts, and the
// canonical grade->variant mapping is `reliabilityBadge` in variants.ts (SSOT).

/** Join class names, dropping falsy values. */
export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** True when the string contains Arabic-script characters. */
export function isRTL(text: string | null | undefined): boolean {
  if (!text) return false;
  return /[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]/.test(text);
}

/** dir attribute value for a piece of text. */
export function dirOf(text: string | null | undefined): "rtl" | "ltr" {
  return isRTL(text) ? "rtl" : "ltr";
}

/** Format a death year as "ت {ah}هـ / {ce}م", omitting missing parts. */
export function formatDeath(ah?: number | null, ce?: number | null): string {
  const parts: string[] = [];
  if (ah != null) parts.push(`ت ${ah}هـ`);
  if (ce != null) parts.push(`${ce}م`);
  return parts.join(" · ");
}

/** First grapheme of the first one or two words — for an avatar mark. */
export function initials(nameAr: string | null | undefined): string {
  if (!nameAr) return "؟";
  const words = nameAr.replace(/[«»ـ]/g, "").split(/\s+/).filter(Boolean);
  if (words.length === 0) return "؟";
  if (words.length === 1) return words[0].slice(0, 2);
  return words[0].charAt(0) + words[1].charAt(0);
}

/** Extract the short id segment from a book urn (last colon-segment). */
export function urnId(urn: string): string {
  const seg = urn.split(":");
  return seg[seg.length - 1] || urn;
}

/** Clamp a number into [min, max]. */
export function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
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
const ARABIC_DIGITS = ["٠", "١", "٢", "٣", "٤", "٥", "٦", "٧", "٨", "٩"];
export function toArabicDigits(value: number | string): string {
  return String(value).replace(/[0-9]/g, (d) => ARABIC_DIGITS[Number(d)]);
}
