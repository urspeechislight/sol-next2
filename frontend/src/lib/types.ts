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

import type { components } from './api/schema';

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
export type CanonicalEntry = Full<S['CanonicalEntry']>;

// ---- catalog + taxonomy (GET /api/books, /api/domains) ----
export type Book = Full<S['Book']>;
export type Category = Full<S['Category']>;
export type Domain = Full<S['Domain']>;
export type CanonicalRank = NonNullable<Book['canonical']>;
export type Tradition = Category['tradition'];

// ---- works (GET /api/works): the volume-folded Library listing ----
export type Work = Full<S['Work']>;

// ---- reader (GET /api/books/{urn}/toc, /pages/{n}) ----
export type TocEntry = Full<S['TocEntry']>;
export type Toc = Full<S['Toc']>;
export type Narrator = Full<S['Narrator']>;
export type CrossRef = Full<S['CrossRef']>;
export type Hadith = Full<S['Hadith']>;
export type BookPage = Full<S['BookPage']>;
export type HadithGrade = NonNullable<Hadith['grade']>;

// ---- daily editorial (GET /api/daily) ----
export type DailyDate = Full<S['DailyDate']>;
export type Tafsir = Full<S['Tafsir']>;
export type Verse = Full<S['Verse']>;
export type HadithSource = Full<S['HadithSource']>;
export type DailyHadith = Full<S['DailyHadith']>;
export type OpenTo = Full<S['OpenTo']>;
export type DailyBookPick = Full<S['DailyBookPick']>;
export type Daily = Full<S['Daily']>;

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
