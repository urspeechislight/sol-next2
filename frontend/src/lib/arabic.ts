// arabic.ts:SSOT for Arabic text folding, mirroring backend patterns.py. Two
// folds for two purposes, sharing one letter-fold rule:
//   - foldSearch / foldSearchChar: the text-SEARCH fold. Strips diacritics +
//     Quranic annotation signs and folds alef/yaa/taa. Mirrors backend
//     fold_search and the corpus index (which is built pre-folded), so the
//     highlighter marks exactly the spans the corpus matched on.
//   - normalizeName / foldNameChar: the name/title fold for narrator linkage.
//     Same letter fold, narrower mark set, collapses whitespace into a
//     comparison key. Mirrors backend normalize_arabic exactly (verified by the
//     shared golden table in tests/fixtures/arabic_fold_golden.json).
// Keep each fold in lockstep with its backend twin. Pure; no DOM.

// Marks stripped for SEARCH — mirror of backend patterns.SEARCH_MARKS:
// arabic signs, harakat, superscript alef, Quranic annotation signs, tatweel.
const SEARCH_MARKS = /[ؐ-ًؚ-ْٰۖ-ۭـ]/;
// Marks stripped for NAME matching — mirror of backend patterns.ARABIC_MARKS.
const NAME_MARKS = /[ً-ْٰـ]/;

/** The one letter-folding rule: unify alef variants, alef-maqsura, taa-marbuta. */
function foldLetter(ch: string): string {
  if (ch === 'أ' || ch === 'إ' || ch === 'آ') return 'ا';
  if (ch === 'ى') return 'ي';
  if (ch === 'ة') return 'ه';
  return ch;
}

/** Fold one character for SEARCH: drop a search-mark, else fold its letter.
    Returns '' for dropped marks, so callers can map folded -> original index. */
export function foldSearchChar(ch: string): string {
  return SEARCH_MARKS.test(ch) ? '' : foldLetter(ch);
}

/** Fold one character for NAME matching (narrower mark set). */
export function foldNameChar(ch: string): string {
  return NAME_MARKS.test(ch) ? '' : foldLetter(ch);
}

/** Fold a whole string for search (diacritics + annotation + letter variants). */
export function foldSearch(s: string): string {
  let out = '';
  for (const ch of s || '') out += foldSearchChar(ch);
  return out;
}

/** Fold a name/title to a comparison key: fold letters, collapse whitespace.
    Mirrors backend ``normalize_arabic`` (drops the same marks, folds the same
    letters, collapses the same whitespace) so the two stacks key names alike. */
export function normalizeName(s: string): string {
  let out = '';
  for (const ch of s || '') out += foldNameChar(ch);
  return out.replace(/\s+/g, ' ').trim();
}
