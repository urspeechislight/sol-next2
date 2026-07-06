// hijri.ts — today's Hijri date from Intl's islamic-umalqura calendar, and
// the app's one English month-name table. The DATE comes from the runtime's
// calendar data; the English month NAMES are ours, because Intl's 'en'
// output renders plain forms ("Muharram") while the app's editorial voice
// uses scholarly transliteration ("Muḥarram"). Arabic names stay with Intl.
// One owner for the English names means the dateline and the almanac can
// never spell the same month two ways on one screen.

export interface HijriToday {
  day: number;
  month: number;
  monthEn: string;
  monthAr: string;
  year: number;
  weekdayEn: string;
  gregorian: string;
}

const HIJRI_MONTHS_EN = [
  'Muḥarram',
  'Ṣafar',
  'Rabīʿ al-Awwal',
  'Rabīʿ al-Thānī',
  'Jumādā al-Ūlā',
  'Jumādā al-Ākhira',
  'Rajab',
  'Shaʿbān',
  'Ramaḍān',
  'Shawwāl',
  'Dhū al-Qaʿda',
  'Dhū al-Ḥijja',
] as const;

/** Scholarly English name of Hijri month 1..12; the number itself when out
    of range (a corrupt value stays visible rather than mislabeled). */
export function hijriMonthName(month: number): string {
  return HIJRI_MONTHS_EN[month - 1] ?? String(month);
}

const HIJRI_CALENDAR = 'islamic-umalqura';

function hijriParts(locale: string, options: Intl.DateTimeFormatOptions): Map<string, string> {
  const fmt = new Intl.DateTimeFormat(`${locale}-u-ca-${HIJRI_CALENDAR}`, options);
  return new Map(fmt.formatToParts(new Date()).map((p) => [p.type, p.value]));
}

/** Today per the Umm al-Qurā reckoning, with the Gregorian date alongside. */
export function hijriToday(): HijriToday {
  const numeric = hijriParts('en', {
    day: 'numeric',
    month: 'numeric',
    year: 'numeric',
    weekday: 'long',
  });
  const monthAr = hijriParts('ar', { month: 'long' });
  const gregorian = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());
  const month = Number(numeric.get('month'));
  return {
    day: Number(numeric.get('day')),
    month,
    monthEn: hijriMonthName(month),
    monthAr: monthAr.get('month') ?? '',
    year: Number(numeric.get('year')),
    weekdayEn: numeric.get('weekday') ?? '',
    gregorian,
  };
}
