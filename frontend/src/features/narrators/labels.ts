// labels.ts: the single place narrator identity fields become human-readable labels
// (and short descriptions), shared by the registry card, the person drawer, and the
// registry filters so tradition/generation/residence vocabulary lives in one spot.

const TRADITION_LABEL: Record<string, string> = {
  both: 'Sunnī + Shīʿī',
  sunni: 'Sunnī',
  shia: 'Shīʿī',
  history: 'History',
};

/** Human label for the corpus a narrator is attested in. */
export function traditionLabel(tradition: string): string {
  return TRADITION_LABEL[tradition] ?? tradition;
}

/** Human label for a derived narrator generation (ṭabaqa). */
export function generationLabel(generation: string): string {
  if (generation === 'companion') return 'Ṣaḥābī';
  if (generation === 'successor') return 'Tābiʿī';
  if (generation === 'successor_of_successors') return 'Tābiʿ al-tābiʿīn';
  return '';
}

/** A filter/legend option carrying a value and its label from the SSOT above. */
export type LabelOption = { value: string; label: string };

/** Ordered tradition options for filters and legends; labels come from the SSOT. */
export const TRADITION_OPTIONS: readonly LabelOption[] = [
  { value: 'sunni', label: TRADITION_LABEL.sunni },
  { value: 'shia', label: TRADITION_LABEL.shia },
  { value: 'both', label: TRADITION_LABEL.both },
  { value: 'history', label: TRADITION_LABEL.history },
];

const RESIDENCE_EN: Record<string, string> = {
  كوفي: 'Kufan',
  مكي: 'Meccan',
  مدني: 'Medinan',
  بصري: 'Basran',
  بغدادي: 'Baghdadi',
  دمشقي: 'Damascene',
  مصري: 'Egyptian',
  شامي: 'Syrian',
  يمني: 'Yemeni',
  رازي: 'of Rayy',
  همداني: 'Hamadhani',
  قمي: 'Qummi',
  خراساني: 'Khurasani',
  واسطي: 'Wasiti',
  أصبهاني: 'Isfahani',
  اصبهاني: 'Isfahani',
  نيسابوري: 'Nishapuri',
  حمصي: 'of Homs',
  قزويني: 'of Qazwin',
  جرجاني: 'of Gurgan',
  مروزي: 'of Merv',
  بلخي: 'Balkhi',
};

/** Render the residence nisbas in English (Kufan, Medinan, …), passing through the rest. */
export function residenceLabel(places: string): string {
  return places
    .split(' | ')
    .map((place) => RESIDENCE_EN[place.trim()] ?? place.trim())
    .join(', ');
}
