// labels.ts: the single place narrator identity fields become human-readable labels
// (and short descriptions), shared by the registry card, the person drawer, and the
// registry filters so tradition/stance/generation/residence vocabulary lives in one spot.

/** Human label for the corpus a narrator is attested in. */
export function traditionLabel(tradition: string): string {
  if (tradition === 'both') return 'Sunnī + Shīʿī';
  if (tradition === 'sunni') return 'Sunnī';
  if (tradition === 'shia') return 'Shīʿī';
  if (tradition === 'history') return 'History';
  return tradition;
}

/** Human label for a derived narrator generation (ṭabaqa). */
export function generationLabel(generation: string): string {
  if (generation === 'companion') return 'Ṣaḥābī';
  if (generation === 'successor') return 'Tābiʿī';
  if (generation === 'successor_of_successors') return 'Tābiʿ al-tābiʿīn';
  return '';
}

const STANCE_LABEL: Record<string, string> = {
  ahlulbayt_member: 'Ahl al-Bayt',
  pro_ahlulbayt: 'Pro-Ahl al-Bayt',
  anti_ahlulbayt: 'Anti-Ahl al-Bayt',
  khariji: 'Khārijī',
};

/** Human label for the recorded stance vis-à-vis the Ahl al-Bayt. */
export function stanceLabel(stance: string): string {
  return STANCE_LABEL[stance] ?? stance;
}

const STANCE_HELP: Record<string, string> = {
  ahlulbayt_member: 'A member of the Prophet’s household.',
  pro_ahlulbayt: 'Recorded as loyal to the Ahl al-Bayt.',
  anti_ahlulbayt: 'Recorded as hostile to the Ahl al-Bayt.',
  khariji: 'Aligned with the Khawārij against ʿAlī.',
};

/** One-line gloss of what a stance token means, for readers new to the vocabulary. */
export function stanceHelp(stance: string): string {
  return STANCE_HELP[stance] ?? '';
}

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
