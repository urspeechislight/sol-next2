// labels.ts: the single place narrator identity fields become human-readable labels
// (and short descriptions), shared by the registry card, the narrator drawer, and
// the registry filters so tradition/category/grade vocabulary lives in one spot.

const TRADITION_LABEL = {
  imami: 'Imāmī',
  shafii: 'Shāfiʿī',
  hanafi: 'Ḥanafī',
  hanbali: 'Ḥanbalī',
  maliki: 'Mālikī',
  zaidi: 'Zaydī',
  ismaili: 'Ismāʿīlī',
  zahiri: 'Ẓāhirī',
};

/** Human label for the school of law a narrator is attested in. */
export function traditionLabel(tradition: string): string {
  return (TRADITION_LABEL as Record<string, string>)[tradition] ?? tradition;
}

/** A filter/legend option carrying a value and its label from the SSOT above. */
export type LabelOption = { value: string; label: string };

/** Ordered tradition options for the registry filters; the values are the
    traditions the registry actually records, labels from the SSOT above. */
export const TRADITION_OPTIONS: readonly LabelOption[] = [
  { value: 'imami', label: TRADITION_LABEL.imami },
  { value: 'shafii', label: TRADITION_LABEL.shafii },
  { value: 'hanafi', label: TRADITION_LABEL.hanafi },
  { value: 'maliki', label: TRADITION_LABEL.maliki },
  { value: 'hanbali', label: TRADITION_LABEL.hanbali },
];

// The grade vocabulary: the Arabic verdict terms as recorded AND their
// normalized tier keys map to one English label each, so a grade renders the
// same label wherever it appears (card chip, drawer rows, tarjama panel).
const GRADE_LABEL: Record<string, string> = {
  ثقه: 'Thiqa · trustworthy',
  مجهول: 'Majhūl · unknown',
  صدوق: 'Ṣadūq · truthful',
  مقبول: 'Maqbūl · acceptable',
  ضعيف: 'Ḍaʿīf · weak',
  متروك: 'Matrūk · abandoned',
  صحابي: 'Ṣaḥābī · companion',
  thiqa: 'Thiqa · trustworthy',
  majhul: 'Majhūl · unknown',
  saduq: 'Ṣadūq · truthful',
  maqbul: 'Maqbūl · acceptable',
  daif: 'Ḍaʿīf · weak',
  matruk: 'Matrūk · abandoned',
  sahabi: 'Ṣaḥābī · companion',
};

/** English label for a grade verdict term (ثقة, مجهول, …) or its normalized
    tier key (thiqa, majhul, …); unknown values pass through unchanged. */
export function gradeLabel(termOrTier: string): string {
  return GRADE_LABEL[termOrTier] ?? termOrTier;
}

const CATEGORY_LABEL = {
  clean: 'Clean',
  long_entry: 'Long entry',
  isnad_fragment: 'Isnād fragment',
};

/** Human label for a narrator entry's data-quality class. */
export function categoryLabel(category: string): string {
  return (CATEGORY_LABEL as Record<string, string>)[category] ?? category;
}

/** Ordered entry-class options for the registry filter; values are the
    classes the registry serves. */
export const CATEGORY_OPTIONS: readonly LabelOption[] = [
  { value: 'clean', label: CATEGORY_LABEL.clean },
  { value: 'long_entry', label: CATEGORY_LABEL.long_entry },
  { value: 'isnad_fragment', label: CATEGORY_LABEL.isnad_fragment },
];

const STANCE_PREDICATE_LABEL: Record<string, string> = {
  'position-toward-ahl-al-bayt': 'Position toward the Ahl al-Bayt',
};

const STANCE_VALUE_LABEL: Record<string, string> = {
  sincere_believer: 'Sincere believer',
  weak_or_erring_believer: 'Weak or erring believer',
  hypocrite_or_hostile: 'Hostile or a hypocrite',
  uncertain: 'Uncertain',
};

/** Human label for an ALID stance predicate (unknown predicates pass through). */
export function stancePredicateLabel(predicate: string): string {
  return STANCE_PREDICATE_LABEL[predicate] ?? predicate;
}

/** Human label for an ALID stance value (unknown values pass through). */
export function stanceValueLabel(value: string): string {
  return STANCE_VALUE_LABEL[value] ?? value;
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
