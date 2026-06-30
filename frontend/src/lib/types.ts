// types.ts:the real sol-next2 :8001 API contract (SSOT). List endpoints return
// Page<T> {items,total,limit,offset}. Both this app and the design components
// bind to these shapes — change them here only when the backend changes.

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ---- narrator registry (GET /api/rijal, /api/canonical) ----

export interface RijalEntry {
  id: number;
  full_name: string;
  kunya: string;
  nisba: string;
  tradition: string;
  death_year: string; // recorded as free-form text (Hijri)
  birth_year: string;
  category: string;
  teacher_count: number;
  student_count: number;
  reliability_term: string;
  reliability_grade: string;
  evaluator: string;
  source_label: string;
  book_path: string;
}

export interface CanonicalEntry {
  canonical_id: number;
  full_name: string;
  kunya: string;
  nisba: string;
  tradition: string;
  death_year: number | null;
  birth_year: number | null;
  entry_count: number;
  source_count: number;
  teacher_count: number;
  student_count: number;
  merge_confidence: number | null;
}

// ---- catalog + taxonomy (GET /api/books, /api/domains) ----

export type CanonicalRank = 'primary' | 'primary_reference' | 'secondary' | 'tertiary';

export interface Book {
  urn: string;
  title_ar: string;
  title_en: string | null;
  author: string | null;
  author_ar: string;
  death_year_ah: number | null;
  death_year_ce: number | null;
  page_count: number | null;
  volume: number | null;
  category: string;
  sect: string | null;
  madhab: string | null;
  canonical: CanonicalRank | null;
  language: string;
  blurb: string | null;
}

export type Tradition = 'sunni' | 'shia' | 'shared';

export interface Category {
  slug: string;
  label: string;
  label_ar: string;
  count: number;
  volume_count: number;
  tradition: Tradition;
}

export interface Domain {
  id: string;
  label: string;
  label_ar: string;
  blurb: string;
  categories: Category[];
}

// ---- works (GET /api/works): the volume-folded Library listing ----
export interface Work {
  stem: string;
  title_ar: string;
  title_en: string | null;
  author: string | null;
  author_ar: string;
  death_year_ah: number | null;
  death_year_ce: number | null;
  page_count: number | null;
  volume_count: number;
  category: string;
  sect: string | null;
  canonical: CanonicalRank | null;
  volumes: string[];
  first_urn: string;
}

// ---- reader (GET /api/books/{urn}/toc, /pages/{n}) ----

export type HadithGrade = 'sahih' | 'hasan' | 'daif' | 'mawdu';

export interface TocEntry {
  page: number;
  title: string;
  title_en: string | null;
  active: boolean;
}

export interface Toc {
  book_urn: string;
  entries: TocEntry[];
}

export interface Narrator {
  name: string;
  name_ar: string;
  role: string;
  grade: string;
  d: number | null;
}

export interface CrossRef {
  book: string;
  book_ar: string;
  chapter: string;
  page: number | null;
}

export interface Hadith {
  n: number;
  isnad_ar: string;
  matn_ar: string;
  matn_en: string | null;
  narrators: Narrator[];
  grade: HadithGrade | null;
  cross_refs: CrossRef[];
}

export interface BookPage {
  page_number: number;
  total_pages: number;
  chapter_title: string;
  chapter_title_en: string | null;
  section_title: string;
  section_title_en: string | null;
  hadiths: Hadith[];
  /** Raw page text, set when the page has no parsed hadiths yet. */
  text_ar: string | null;
}

// ---- daily editorial (GET /api/daily) ----

export interface DailyDate {
  hijri: string;
  hijri_short: string;
  gregorian: string;
}

export interface Tafsir {
  book: string;
  book_ar: string;
  author: string;
  urn: string;
  excerpt_en: string;
  excerpt_ar: string;
}

export interface Verse {
  surah: string;
  surah_ar: string;
  surah_n: number;
  ayah_n: number;
  ayah_ar: string;
  ayah_en: string;
  tafsirs: Tafsir[];
}

export interface HadithSource {
  book: string;
  book_ar: string;
  n: string;
  urn: string | null;
  sect: string;
}

export interface DailyHadith {
  matn_ar: string;
  matn_en: string;
  isnad_ar: string;
  source: HadithSource;
  parallels: HadithSource[];
  grade: HadithGrade;
  grade_label: string;
  note: string;
}

export interface OpenTo {
  page: number;
  chapter_en: string;
}

export interface DailyBookPick {
  urn: string;
  rationale: string;
  open_to: OpenTo;
}

export interface Daily {
  date: DailyDate;
  verse: Verse;
  hadith: DailyHadith;
  book: DailyBookPick;
  rotation: string[];
}

// ---- narrator tarjama (DERIVED view-type) ----
// Reading text carries no narrator IDs, so narrators are joined to the rijāl /
// canonical registries BY NAME. NarratorRecord is the merged shape the reader
// surfaces; it is composed client-side from RijalEntry + CanonicalEntry.
export interface NarratorRecord {
  id: number;
  full_name: string;
  kunya: string;
  nisba: string;
  tradition: string;
  birth_year: string;
  death_year: string;
  teacher_count: number;
  student_count: number;
  reliability_term?: string | null;
  reliability_grade?: string | null;
  evaluator?: string | null;
  source_label?: string | null;
  merge_confidence?: number | null;
  origin: 'rijal' | 'canonical';
}

// ---- share (UI feature, generic; not backend-bound) ----
// ShareFormat is derived from SHARE_FORMATS in constants.ts (the runtime options).

export interface ShareContent {
  kicker: string;
  arabic: string;
  latin: string;
  source: string;
  url: string;
}

export interface ShareResponse {
  short_url: string;
  caption: string;
  qr: boolean[][];
  image_url: string | null;
}

// GET /api/books/{urn}/search
export interface BookSearchMatch {
  page: number;
  snippet: string;
}

// GET /api/search (cross-corpus full-text)
export interface CorpusMatch {
  urn: string;
  title_ar: string;
  title_en: string | null;
  author: string | null;
  category: string;
  volume: number | null;
  page: number;
  snippet: string;
}

// GET /api/search/facets — drill-down: category -> book -> volume
export interface CategoryFacet {
  slug: string;
  count: number;
}

export interface BookFacet {
  title: string;
  title_en: string | null;
  count: number;
}

export interface VolumeFacet {
  volume: number;
  count: number;
}

export interface SearchFacets {
  categories: CategoryFacet[];
  books: BookFacet[];
  volumes: VolumeFacet[];
}

// GET /api/quran/{surah}/{ayah} — one verse, pointed + bare forms
export interface Ayah {
  surah: number;
  ayah: number;
  verse_count: number;
  text_ar: string;
  text_plain: string;
  text_en: string | null;
}
