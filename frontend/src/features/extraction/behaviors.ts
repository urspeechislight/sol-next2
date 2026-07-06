// behaviors.ts:the extraction inspector's one mapping of routing-table
// behavior labels onto chip tone classes (extraction.css resolves each tone
// to a content-semantic token). A behavior the map does not know yet renders
// the neutral tone: the label itself is always printed, color is only a
// secondary scanning channel, and new routing-table labels must not crash
// the validation surface built to inspect them.

const BEHAVIOR_TONES: Record<string, string> = {
  HADITH_TRANSMISSION: 'hadith',
  QURAN_VERSE: 'quran',
  BASMALA: 'quran',
  AUTHOR_COMMENTARY: 'commentary',
  FIQH_RULING: 'ruling',
  NUMBERED_ENTRY: 'entry',
  SECTION_HEADING: 'heading',
  POETRY: 'poetry',
  BIOGRAPHY: 'biography',
  GENERAL_PROSE: 'prose',
  EDITORIAL_FRONTMATTER: 'editorial',
};

/** Tone class suffix for one behavior label. */
export function behaviorTone(behavior: string): string {
  return BEHAVIOR_TONES[behavior] ?? 'neutral';
}
