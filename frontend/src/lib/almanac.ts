// almanac.ts — the landing page's calendar observances and on-this-day events.
//
// PLACEHOLDER DATA: these tables are a curated editorial seed so the landing
// page renders a complete experience before the corpus feeds it. Dates follow
// the common Twelver reckoning; observed dates vary by moon-sighting and
// community. Replace with a served dataset when the pipeline provides one.

export type ObservanceKind = 'eid' | 'mourning' | 'birth' | 'night' | 'observance';

export interface Observance {
  month: number;
  day: number;
  en: string;
  ar: string;
  kind: ObservanceKind;
}

export interface HistoryEvent {
  month: number;
  day: number;
  yearAh: number;
  en: string;
  detail: string;
}

export const OBSERVANCES: readonly Observance[] = [
  { month: 1, day: 1, en: 'Hijri New Year', ar: 'رأس السنة الهجرية', kind: 'observance' },
  { month: 1, day: 9, en: 'Tāsūʿāʾ', ar: 'تاسوعاء', kind: 'mourning' },
  { month: 1, day: 10, en: 'ʿĀshūrāʾ', ar: 'عاشوراء', kind: 'mourning' },
  {
    month: 1,
    day: 25,
    en: 'Martyrdom of Imām al-Sajjād',
    ar: 'شهادة الإمام السجاد',
    kind: 'mourning',
  },
  { month: 2, day: 20, en: 'Arbaʿīn', ar: 'الأربعين', kind: 'mourning' },
  {
    month: 2,
    day: 28,
    en: 'Passing of the Prophet ﷺ · Martyrdom of Imām al-Ḥasan',
    ar: 'وفاة النبي ﷺ وشهادة الإمام الحسن',
    kind: 'mourning',
  },
  {
    month: 3,
    day: 8,
    en: 'Martyrdom of Imām al-ʿAskarī',
    ar: 'شهادة الإمام العسكري',
    kind: 'mourning',
  },
  {
    month: 3,
    day: 17,
    en: 'Mawlid al-Nabī ﷺ · Birth of Imām al-Ṣādiq',
    ar: 'المولد النبوي وولادة الإمام الصادق',
    kind: 'birth',
  },
  { month: 5, day: 5, en: 'Birth of Sayyida Zaynab', ar: 'ولادة السيدة زينب', kind: 'birth' },
  {
    month: 6,
    day: 3,
    en: 'Martyrdom of Sayyida Fāṭima',
    ar: 'شهادة السيدة فاطمة',
    kind: 'mourning',
  },
  { month: 6, day: 20, en: 'Birth of Sayyida Fāṭima', ar: 'ولادة السيدة فاطمة', kind: 'birth' },
  { month: 7, day: 1, en: 'Birth of Imām al-Bāqir', ar: 'ولادة الإمام الباقر', kind: 'birth' },
  { month: 7, day: 10, en: 'Birth of Imām al-Jawād', ar: 'ولادة الإمام الجواد', kind: 'birth' },
  { month: 7, day: 13, en: 'Birth of Imām ʿAlī', ar: 'ولادة الإمام علي', kind: 'birth' },
  {
    month: 7,
    day: 25,
    en: 'Martyrdom of Imām al-Kāẓim',
    ar: 'شهادة الإمام الكاظم',
    kind: 'mourning',
  },
  { month: 7, day: 27, en: 'al-Mabʿath', ar: 'المبعث النبوي', kind: 'observance' },
  { month: 8, day: 3, en: 'Birth of Imām al-Ḥusayn', ar: 'ولادة الإمام الحسين', kind: 'birth' },
  { month: 8, day: 4, en: 'Birth of al-ʿAbbās', ar: 'ولادة العباس بن علي', kind: 'birth' },
  { month: 8, day: 5, en: 'Birth of Imām al-Sajjād', ar: 'ولادة الإمام السجاد', kind: 'birth' },
  {
    month: 8,
    day: 15,
    en: 'Mid-Shaʿbān · Birth of Imām al-Mahdī',
    ar: 'النصف من شعبان وولادة الإمام المهدي',
    kind: 'birth',
  },
  { month: 9, day: 10, en: 'Passing of Khadīja', ar: 'وفاة السيدة خديجة', kind: 'mourning' },
  { month: 9, day: 15, en: 'Birth of Imām al-Ḥasan', ar: 'ولادة الإمام الحسن', kind: 'birth' },
  {
    month: 9,
    day: 21,
    en: 'Martyrdom of Imām ʿAlī',
    ar: 'شهادة الإمام علي',
    kind: 'mourning',
  },
  { month: 9, day: 23, en: 'Laylat al-Qadr', ar: 'ليلة القدر', kind: 'night' },
  { month: 10, day: 1, en: 'ʿĪd al-Fiṭr', ar: 'عيد الفطر', kind: 'eid' },
  {
    month: 10,
    day: 25,
    en: 'Martyrdom of Imām al-Ṣādiq',
    ar: 'شهادة الإمام الصادق',
    kind: 'mourning',
  },
  { month: 11, day: 11, en: 'Birth of Imām al-Riḍā', ar: 'ولادة الإمام الرضا', kind: 'birth' },
  {
    month: 11,
    day: 29,
    en: 'Martyrdom of Imām al-Jawād',
    ar: 'شهادة الإمام الجواد',
    kind: 'mourning',
  },
  { month: 12, day: 9, en: 'Day of ʿArafa', ar: 'يوم عرفة', kind: 'observance' },
  { month: 12, day: 10, en: 'ʿĪd al-Aḍḥā', ar: 'عيد الأضحى', kind: 'eid' },
  { month: 12, day: 15, en: 'Birth of Imām al-Hādī', ar: 'ولادة الإمام الهادي', kind: 'birth' },
  { month: 12, day: 18, en: 'ʿĪd al-Ghadīr', ar: 'عيد الغدير', kind: 'eid' },
  { month: 12, day: 24, en: 'Day of Mubāhala', ar: 'يوم المباهلة', kind: 'observance' },
] as const;

export const HISTORY_EVENTS: readonly HistoryEvent[] = [
  {
    month: 1,
    day: 10,
    yearAh: 61,
    en: 'The Battle of Karbalāʾ',
    detail:
      'Imām al-Ḥusayn and his companions were killed on the plain of Karbalāʾ, a rupture mourned and retold in every century since.',
  },
  {
    month: 2,
    day: 28,
    yearAh: 11,
    en: 'The Prophet ﷺ passes in Medina',
    detail:
      'After the farewell pilgrimage, the Prophet ﷺ died in the house of ʿĀʾisha and was buried where he passed, in what is now the Prophet’s Mosque.',
  },
  {
    month: 3,
    day: 12,
    yearAh: 1,
    en: 'Arrival at Medina',
    detail:
      'The hijra concluded: the Prophet ﷺ reached Qubāʾ and then Yathrib, and the community that would carry the tradition took form.',
  },
  {
    month: 7,
    day: 27,
    yearAh: 0,
    en: 'The first revelation proclaimed',
    detail:
      'Per the Twelver reckoning of al-Mabʿath, the Prophet ﷺ was commissioned on 27 Rajab, thirteen years before the hijra.',
  },
  {
    month: 9,
    day: 17,
    yearAh: 2,
    en: 'The Battle of Badr',
    detail:
      'Three hundred and thirteen met a force three times their size at the wells of Badr; the victory fixed the young community’s standing.',
  },
  {
    month: 9,
    day: 21,
    yearAh: 40,
    en: 'Imām ʿAlī dies of his wound',
    detail:
      'Struck at dawn prayer in the mosque of Kūfa two days earlier, ʿAlī ibn Abī Ṭālib died on the 21st of Ramaḍān.',
  },
  {
    month: 10,
    day: 2,
    yearAh: 8,
    en: 'The conquest of Mecca consolidated',
    detail:
      'In the days after the city opened, the Kaʿba was cleared of idols and the old order of Quraysh yielded without a battle.',
  },
  {
    month: 8,
    day: 15,
    yearAh: 255,
    en: 'Birth of Imām al-Mahdī',
    detail:
      'In Sāmarrāʾ, the twelfth Imām was born to Imām al-ʿAskarī; the Twelver tradition dates the minor occultation from his father’s death.',
  },
  {
    month: 12,
    day: 18,
    yearAh: 10,
    en: 'The pond of Ghadīr Khumm',
    detail:
      'Returning from the farewell pilgrimage, the Prophet ﷺ halted the caravans at Ghadīr Khumm and raised ʿAlī’s hand before the assembly.',
  },
  {
    month: 4,
    day: 8,
    yearAh: 260,
    en: 'Death of Imām al-ʿAskarī',
    detail:
      'The eleventh Imām died in Sāmarrāʾ under ʿAbbāsid watch; with him began the era of the four deputies.',
  },
] as const;

// Rotor stride for the no-exact-match pick: co-prime with the table length so
// consecutive days walk the whole table instead of repeating a short cycle.
const ROTOR_STRIDE = 31;

/** Observances of one Hijri month, day-ordered. */
export function observancesForMonth(month: number): Observance[] {
  return OBSERVANCES.filter((o) => o.month === month).sort((a, b) => a.day - b.day);
}

export interface TodayInHistory {
  event: HistoryEvent;
  onThisDay: boolean;
}

/** The event shown as "today in history": an exact Hijri-day match when one
    exists, otherwise a deterministic pick that rotates daily through the
    table (flagged so the UI says "from this era", not "on this day"). */
export function eventForDay(month: number, day: number): TodayInHistory {
  const exact = HISTORY_EVENTS.find((e) => e.month === month && e.day === day);
  if (exact) return { event: exact, onThisDay: true };
  const index = (month * ROTOR_STRIDE + day) % HISTORY_EVENTS.length;
  return { event: HISTORY_EVENTS[index], onThisDay: false };
}
