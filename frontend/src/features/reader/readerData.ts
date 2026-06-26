// readerData.ts — mock reading data for the Reader (ported from Reader.html).
// Narrator linkage uses the narrators.ts SSOT; records are keyed on the text
// form (`match`) so names link inside the gold isnād line.
import type { NarratorRecord } from "../../lib/types";

export interface ReaderNarrator {
  id: string;
  fullName: string;
  match: string;
  en: string;
  kunya: string;
  nisba: string;
  tradition: string;
  birthYear: string;
  deathYear: string;
  teacherCount: number;
  studentCount: number;
  term: string;
  grade: string;
  evaluator: string;
  role: string;
}

export const NARRATORS: ReaderNarrator[] = [
  { id: "n0", fullName: "الإمام الصادق عليه", match: "الإمام الصادق عليه", en: "Imām al-Ṣādiq (ʿa)", kunya: "أبو عبد الله", nisba: "الهاشمي", tradition: "Imām", birthYear: "83 AH", deathYear: "148 AH", teacherCount: 0, studentCount: 4000, term: "معصوم", grade: "masum", evaluator: "", role: "Origin" },
  { id: "n1", fullName: "علي بن إبراهيم القمي", match: "علي بن إبراهيم", en: "ʿAli ibn Ibrahim al-Qummi", kunya: "أبو الحسن", nisba: "القمي", tradition: "Imāmī", birthYear: "", deathYear: "307 AH", teacherCount: 34, studentCount: 50, term: "ثقة", grade: "thiqa", evaluator: "al-Najāshī", role: "Compiler’s teacher" },
  { id: "n2", fullName: "إبراهيم بن هاشم", match: "إبراهيم بن هاشم", en: "Ibrahim ibn Hashim", kunya: "أبو إسحاق", nisba: "القمي", tradition: "Imāmī", birthYear: "", deathYear: "245 AH", teacherCount: 40, studentCount: 60, term: "ثقة", grade: "thiqa", evaluator: "al-ʿAllāma", role: "Father of ʿAli" },
  { id: "n3", fullName: "العباس بن عمرو الفقيمي", match: "العباس بن عمرو الفقيمي", en: "al-ʿAbbas ibn ʿAmr al-Fuqaymi", kunya: "", nisba: "الفقيمي", tradition: "Imāmī", birthYear: "", deathYear: "270 AH", teacherCount: 8, studentCount: 12, term: "صدوق", grade: "saduq", evaluator: "al-Khūʾī", role: "Transmitter" },
  { id: "n4", fullName: "هشام بن الحكم", match: "هشام بن الحكم", en: "Hisham ibn al-Hakam", kunya: "أبو محمد", nisba: "الكندي", tradition: "Imāmī", birthYear: "", deathYear: "199 AH", teacherCount: 6, studentCount: 30, term: "ثقة ثبت", grade: "thiqa thabt", evaluator: "al-Kashshī", role: "Companion of al-Ṣādiq" },
];

export const CHAIN_ORDER = ["n0", "n1", "n2", "n3", "n4"];

export interface HadithRef {
  ar: string;
  pg: string;
}
export interface ReaderHadith {
  num: string;
  narrators: number;
  grade: string;
  isnadAr: string;
  isnadEn: string;
  matnAr: string;
  matnEn: string;
  refs: HadithRef[];
}

export const HADITHS: ReaderHadith[] = [
  {
    num: "١", narrators: 4, grade: "صحيح",
    isnadAr: "عَلِيُّ بْنُ إِبْرَاهِيمَ، عَنْ أَبِيهِ، عَنِ الْعَبَّاسِ بْنِ عَمْرٍو الْفُقَيْمِيِّ، عَنْ هِشَامِ بْنِ الْحَكَمِ، فِي حَدِيثِ الزِّنْدِيقِ الَّذِي أَتَى أَبَا عَبْدِ اللَّهِ عليه",
    isnadEn: "ʿAlī b. Ibrāhīm, from his father, from al-ʿAbbās b. ʿAmr al-Fuqaymī, from Hishām b. al-Ḥakam, in the tradition of the heretic who came to Abū ʿAbd Allāh (a.s.).",
    matnAr: "فَكَانَ مِنْ سُؤَالِهِ أَنْ قَالَ: كَيْفَ يَعْبُدُ اللَّهَ الْخَلْقُ وَلَمْ يَرَوْهُ؟ قَالَ عليه: «رَأَتْهُ الْقُلُوبُ بِنُورِ الْإِيمَانِ، وَأَثْبَتَتْهُ الْعُقُولُ بِيَقَظَتِهَا إِثْبَاتَ الْعَيَانِ، وَالْأَبْصَارُ لَا تُدْرِكُهُ، وَهُوَ يُدْرِكُ الْأَبْصَارَ، وَهُوَ اللَّطِيفُ الْخَبِيرُ».",
    matnEn: "Among his questions was: “How can creation worship God whom they have not seen?” He (peace be upon him) replied: “Hearts have seen Him by the light of faith, and intellects have affirmed Him with their wakefulness as one affirms what is witnessed; sight does not perceive Him, yet He perceives sight, He is the Subtle, the Aware.”",
    refs: [{ ar: "بحار الأنوار", pg: "p.44" }, { ar: "التوحيد للصدوق", pg: "p.108" }],
  },
  {
    num: "٢", narrators: 4, grade: "صحيح",
    isnadAr: "عِدَّةٌ مِنْ أَصْحَابِنَا، عَنْ أَحْمَدَ بْنِ مُحَمَّدٍ، عَنِ الْحُسَيْنِ بْنِ سَعِيدٍ، عَنِ النَّضْرِ بْنِ سُوَيْدٍ، عَنْ هِشَامِ بْنِ الْحَكَمِ",
    isnadEn: "A number of our companions, from Aḥmad b. Muḥammad, from al-Ḥusayn b. Saʿīd, from al-Naḍr b. Suwayd, from Hishām b. al-Ḥakam.",
    matnAr: "قَالَ: قُلْتُ لِأَبِي عَبْدِ اللَّهِ عليه: مَا الدَّلِيلُ عَلَى أَنَّ لِلْعَالَمِ صَانِعًا؟ قَالَ: «وُجُودُ الْأَفَاعِيلِ الَّتِي دَلَّتْ عَلَى أَنَّ صَانِعًا صَنَعَهَا».",
    matnEn: "He said: I said to Abū ʿAbd Allāh (a.s.): what is the proof that the world has a Maker? He replied: “The existence of effects which indicate that a Maker made them.”",
    refs: [{ ar: "التوحيد للصدوق", pg: "p.250" }],
  },
];

export interface TocEntry {
  ar: string;
  en: string;
  pg: number;
  current?: boolean;
}
export const TOC: TocEntry[] = [
  { ar: "مقدمة المؤلف", en: "Author’s Introduction", pg: 1 },
  { ar: "كتاب العقل والجهل", en: "The Book of Intellect and Ignorance", pg: 11 },
  { ar: "كتاب فضل العلم", en: "The Book of the Excellence of Knowledge", pg: 47 },
  { ar: "كتاب التوحيد", en: "The Book of Divine Unity", pg: 109, current: true },
  { ar: "كتاب الحجة", en: "The Book of the Proof", pg: 184 },
  { ar: "كتاب الإيمان والكفر", en: "The Book of Faith and Disbelief", pg: 421 },
  { ar: "كتاب الدعاء", en: "The Book of Supplication", pg: 612 },
  { ar: "كتاب فضل القرآن", en: "The Book of the Excellence of the Qurʾan", pg: 738 },
  { ar: "كتاب العشرة", en: "The Book of Social Conduct", pg: 791 },
];

export interface SearchMatch {
  pg: number;
  ar: string;
  en: string;
}
export const MATCHES: SearchMatch[] = [
  { pg: 44, ar: "رَأَتْهُ الْقُلُوبُ بِنُورِ الْإِيمَانِ", en: "Hearts have seen Him by the light of faith…" },
  { pg: 44, ar: "وَهُوَ اللَّطِيفُ الْخَبِيرُ", en: "He is the Subtle, the Aware…" },
  { pg: 50, ar: "وُجُودُ الْأَفَاعِيلِ", en: "The existence of effects…" },
];

/** Build NarratorRecord[] keyed on the text-match form for narrators.ts linkage. */
export function narratorRecords(): NarratorRecord[] {
  return NARRATORS.map((n) => ({
    id: n.id, full_name: n.match, kunya: n.kunya, nisba: n.nisba, tradition: n.tradition,
    birth_year: n.birthYear, death_year: n.deathYear, teacher_count: n.teacherCount,
    student_count: n.studentCount, reliability_term: n.term, reliability_grade: n.grade,
    evaluator: n.evaluator, origin: "rijal",
  }));
}

/** Latin label for a grade key (isnād + chain). */
export function engGrade(g: string): string {
  const s = (g || "").toLowerCase();
  if (/masum/.test(s)) return "MAṢŪM";
  if (/(thiqa|thabt|hafiz|imam|hujja)/.test(s)) return "TRUSTWORTHY";
  if (/(saduq|hasan|maqbul)/.test(s)) return "RELIABLE";
  if (/(daif|matruk|kadhdhab|weak)/.test(s)) return "WEAK";
  if (/majhul/.test(s)) return "UNKNOWN";
  return s.toUpperCase();
}

/** Isnād node grade tone (empty = success/neutral). */
export function isnadTone(g: string): string {
  const s = (g || "").toLowerCase();
  if (/(daif|matruk|kadhdhab|weak)/.test(s)) return "danger";
  if (/majhul/.test(s)) return "warning";
  return "";
}

/** Tarjama reliability-grade tone. */
export function relTone(g: string): string {
  const s = (g || "").toLowerCase();
  if (/(sahih|thiqa|thabt|hafiz|hujja|imam|reliable|strong|sound)/.test(s)) return "success";
  if (/(saduq|maqbul|hasan|acceptable|fair|truthful)/.test(s)) return "warning";
  if (/(daif|matruk|majhul|kadhdhab|weak|liar)/.test(s)) return "danger";
  return "default";
}
