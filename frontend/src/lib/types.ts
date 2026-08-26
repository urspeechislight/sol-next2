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

// A fresh empty page envelope, so the empty-result literal lives in one place.
export function emptyPage<T>(): Page<T> {
  return { items: [], total: 0, limit: 0, offset: 0 };
}

// ---- narrator registry (GET /api/narrators) ----
export type NarratorEntry = Full<S['NarratorEntry']>;
export type NarratorDetail = Full<S['NarratorDetail']>;
export type NarratorAlias = Full<S['NarratorAliasOut']>;
export type NarratorGrade = Full<S['NarratorGradeOut']>;
/** One ALID stance claim: {predicate, value_text} pairs served as a string map. */
export type NarratorStance = NarratorDetail['stances'][number];
export type NarratorGraph = Full<S['NarratorGraph']>;
export type NarratorGraphNode = Full<S['NarratorGraphNode']>;
export type NarratorGraphEdge = Full<S['NarratorGraphEdge']>;

// ---- health (GET /api/health): the subsystem heartbeat ----
export type HealthReport = Full<S['HealthReport']>;
export type HealthCheck = Full<S['HealthCheck']>;

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
// Reading text joins narrators to the registry by NAME (the served Narrator
// carries a build-time narrator_id link, but the page text does not).
// NarratorRecord is the merged shape the reader surfaces: the in-text
// narrator (name + death year + link) overlaid by NarratorDetail when the
// registry knows the narrator. id -1 marks an unlinked text narrator.
export interface NarratorRecord {
  /** Registry id; -1 when the text's narrator has no registry entry. */
  id: number;
  /** The served Narrator's link, echoed so linked and fetched records stay
      distinguishable; null when the text carried no link. */
  narrator_id: number | null;
  primary_name_ar: string;
  primary_name_en: string;
  kunya: string;
  nisba: string;
  tradition: string;
  birth_year_ah: number | null;
  death_year_ah: number | null;
  death_year_ce: string;
  teacher_count: number;
  student_count: number;
  /** Top reliability tier (thiqa, saduq, …) when any grade is recorded. */
  tier: string | null;
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
