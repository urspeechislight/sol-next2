// types.ts — real sol-next API contract (Part F). Fixed interface; copied verbatim.
// All list endpoints return Paginated<T> with ?page=&per_page=.

export interface Paginated<T> {
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  entries: T[];
}

// GET /api/rijal
export interface RijalEntry {
  id: string;
  full_name: string;
  kunya: string;
  nisba: string;
  tradition: string;
  death_year: string; // STRING
  birth_year: string; // STRING
  category: string;
  teacher_count: number;
  student_count: number;
  reliability_term: string;
  reliability_grade: string;
  evaluator: string;
  source_label: string;
  book_path: string;
}

// GET /api/canonical
export interface CanonicalEntry {
  canonical_id: string;
  full_name: string;
  kunya: string;
  nisba: string;
  tradition: string;
  death_year: number; // NUMBER
  birth_year: number; // NUMBER
  entry_count: number;
  source_count: number;
  teacher_count: number;
  student_count: number;
  merge_confidence: number | null;
}

// GET /api/history
export interface HistoryEntry {
  id: string;
  full_name: string;
  kunya: string;
  nisba: string;
  title: string;
  death_year: number;
  birth_year: number;
  event_count: number;
  event_types: string[];
}

export interface BehaviorSummary {
  behavior: string;
  count: number;
}

// GET /api/data
export interface BookData {
  work_id: string;
  manifestation_id: string;
  title: string;
  author: string;
  book_path: string;
  book_slug: string;
  total_pages: number;
  content_pages: number;
  skipped_pages: number;
  total_spans: number;
  behavior_count: number;
  behavior_summary: BehaviorSummary[];
}

export interface BookCatalogEntry {
  path: string;
  filename: string;
  display: string;
  slug: string;
}

// GET /api/books -> BookGenre[]
export interface BookGenre {
  genre: string;
  genre_id: string;
  books: BookCatalogEntry[];
}

// PROVISIONAL reading shape — bind the reader to THIS, nothing richer.
export interface ReaderPage {
  book_slug: string;
  page_number: number;
  total_pages: number;
  heading?: string | null;
  units: ReaderUnit[];
}

export interface ReaderUnit {
  id: string;
  text_ar: string;
  text_en?: string | null;
  kind?: string | null; // free string; NOT a hadith taxonomy
}

// Share is PROVISIONAL — keep the Share UI; ShareContent stays generic.
// Stage-2 reconciliation: ShareFormat was referenced by ShareCard/ShareSheet but
// missing from the source; restored here as the three card aspect-ratios.
export type ShareFormat = "link" | "square" | "story";

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
  image_url?: string | null;
}

// ---- Narrator tarjama (DERIVED view-type) ----
// Reading text carries no narrator IDs, so narrators are joined to the rijāl /
// canonical registries BY NAME. NarratorRecord is the merged shape the reader
// surfaces; it is composed client-side from RijalEntry + CanonicalEntry.
export interface NarratorRecord {
  id: string;
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
  origin: "rijal" | "canonical";
}
