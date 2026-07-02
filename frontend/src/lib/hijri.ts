// hijri.ts — today's Hijri date from Intl's islamic-umalqura calendar. The
// runtime's calendar data is the source; no dependency, no lookup tables.
// Numeric and named parts come from formatToParts so callers can compose
// Arabic and Latin renderings independently.

export interface HijriToday {
  day: number;
  month: number;
  monthEn: string;
  monthAr: string;
  year: number;
  weekdayEn: string;
  gregorian: string;
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
  const monthEn = hijriParts('en', { month: 'long' });
  const monthAr = hijriParts('ar', { month: 'long' });
  const gregorian = new Intl.DateTimeFormat('en-GB', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date());
  return {
    day: Number(numeric.get('day')),
    month: Number(numeric.get('month')),
    monthEn: monthEn.get('month') ?? '',
    monthAr: monthAr.get('month') ?? '',
    year: Number(numeric.get('year')),
    weekdayEn: numeric.get('weekday') ?? '',
    gregorian,
  };
}
