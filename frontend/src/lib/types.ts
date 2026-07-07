// types.ts:the sol-next2 :8001 API contract, generated — not hand-mirrored.
// The wire shapes come from src/lib/api/schema.d.ts, which openapi-typescript
// generates from frontend/openapi.json (itself exported from the backend by
// scripts/export_openapi.py). Regenerate both with `pnpm types:gen`; ci fails
// if they drift from the backend.
//
// Full<> restores field presence: pydantic marks defaulted fields as
// non-required in OpenAPI, but FastAPI responses always serialize every
// field, so the truthful contract is "always present, possibly null".
// Page<T> stays hand-written because the schema can only express the
// monomorphized Page_Book_/Page_Ayah_/... forms of the one generic envelope.

import type { components, operations } from './api/schema';

type S = components['schemas'];

type Full<T> = T extends (infer U)[]
  ? Full<U>[]
  : T extends object
    ? { [K in keyof T]-?: Full<T[K]> }
    : T;

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// ---- narrator registry (GET /api/rijal, /api/canonical) ----
export type RijalEntry = Full<S['RijalEntry']>;
export type PersonEntry = Full<S['PersonEntry']>;
export type PersonEdge = Full<S['PersonEdge']>;

// ---- catalog + taxonomy (GET /api/books, /api/domains) ----
export type Book = Full<S['Book']>;
export type Category = Full<S['Category']>;
export type Domain = Full<S['Domain']>;
export type CanonicalRank = NonNullable<Book['canonical']>;
export type Tradition = Category['tradition'];

// ---- works (GET /api/works): the volume-folded Library listing ----
export type Work = Full<S['Work']>;
/** The closed works-ordering set, straight from the served ?sort= contract
    (an unknown value 422s server-side), so a new backend ordering appears
    here on the next types:gen instead of drifting in a hand copy. */
export type WorkSort = NonNullable<
  NonNullable<operations['_list_works_api_works_get']['parameters']['query']>['sort']
>;

// ---- content search (GET /api/search) ----
/** The closed match-mode set from the served ?mode= contract (backend
    models/search.py owns the vocabulary). */
export type SearchMode = NonNullable<
  NonNullable<operations['_search_api_search_get']['parameters']['query']>['mode']
>;

// ---- reader (GET /api/books/{urn}/toc, /pages/{n}) ----
export type TocEntry = Full<S['TocEntry']>;
export type Toc = Full<S['Toc']>;
export type Narrator = Full<S['Narrator']>;
export type CrossRef = Full<S['CrossRef']>;
export type Hadith = Full<S['Hadith']>;
export type Footnote = Full<S['Footnote']>;
export type BookPage = Full<S['BookPage']>;
export type HadithGrade = NonNullable<Hadith['grade']>;

// ---- daily editorial (GET /api/daily) ----
export type Tafsir = Full<S['Tafsir']>;
export type Verse = Full<S['Verse']>;
export type HadithSource = Full<S['HadithSource']>;
export type DailyHadith = Full<S['DailyHadith']>;
export type OpenTo = Full<S['OpenTo']>;
export type DailyBookPick = Full<S['DailyBookPick']>;
export type Daily = Full<S['Daily']>;

// ---- almanac (GET /api/almanac) ----
export type Observance = Full<S['Observance']>;
export type HistoryEvent = Full<S['HistoryEvent']>;
export type Almanac = Full<S['Almanac']>;

// ---- dev extraction inspection (GET /api/dev/extraction/*) ----
export type ExtractionPattern = Full<S['ExtractionPattern']>;
export type ExtractionSpan = Full<S['ExtractionSpan']>;
export type ExtractionUnit = Full<S['ExtractionUnit']>;
export type ExtractionEntity = Full<S['ExtractionEntity']>;
export type ExtractionPage = Full<S['ExtractionPage']>;
export type BehaviorCount = Full<S['BehaviorCount']>;
export type ExtractionBookSummary = Full<S['ExtractionBookSummary']>;
export type EntrySectionAudit = Full<S['EntrySectionAudit']>;
export type ExtractionEntryAudit = Full<S['ExtractionEntryAudit']>;

// ---- search (GET /api/search, /search/facets, /books/{urn}/search) ----
export type BookSearchMatch = Full<S['BookSearchMatch']>;
export type CorpusMatch = Full<S['CorpusMatch']>;
export type CategoryFacet = Full<S['CategoryFacet']>;
export type BookFacet = Full<S['BookFacet']>;
export type VolumeFacet = Full<S['VolumeFacet']>;
export type SearchFacets = Full<S['SearchFacets']>;

// ---- quran (GET /api/quran/{surah}, /quran/{surah}/{ayah}, /quran/search) ----
export type Ayah = Full<S['Ayah']>;
export type Surah = Full<S['Surah']>;
export type QuranCitation = Full<S['Citation']>;

// ---- narrator tarjama (DERIVED view-type) ----
// Reading text carries no narrator IDs, so narrators are joined to the rijāl /
// person registries BY NAME. NarratorRecord is the merged shape the reader
// surfaces; it is composed client-side from RijalEntry + PersonEntry.
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
  stance?: string | null;
  origin: 'rijal' | 'person';
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
