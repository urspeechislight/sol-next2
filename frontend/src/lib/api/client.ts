// client.ts:the only data path to the :8001 backend (proxied via vite /api).
// Every call is a GET; failures throw ApiError (fail loud, no silent fallback)
// so callers render an explicit error state. CENTRAL-007 confines fetch here.
import { PAGE, SEARCH } from '../constants';
import { API } from '../routes';
import type {
  Almanac,
  Ayah,
  Book,
  BookPage,
  BookSearchMatch,
  CanonicalEntry,
  CanonicalRank,
  CorpusMatch,
  Daily,
  Domain,
  Page,
  QuranCitation,
  RijalEntry,
  SearchFacets,
  SearchMode,
  Surah,
  Toc,
  Work,
  WorkSort,
} from '../types';

class ApiError extends Error {
  status: number;
  url: string;
  constructor(status: number, url: string) {
    super(`API ${status}: ${url}`);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
  }
}

type QueryValue = string | number | boolean | readonly string[];

async function get<T>(path: string): Promise<T> {
  const url = `${API.BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, url);
  return (await res.json()) as T;
}

/** Build a query string, dropping empty strings and false flags. An array
    value appends one repeated param per entry (the set-valued filters). */
function query(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === '' || value === false) continue;
    if (Array.isArray(value)) {
      for (const entry of value) search.append(key, entry);
      continue;
    }
    search.set(key, String(value));
  }
  const qs = search.toString();
  return qs ? `?${qs}` : '';
}

// ---- catalog + taxonomy ----

export function getDomains(): Promise<Domain[]> {
  return get<Domain[]>(API.DOMAINS);
}

export function getBook(urn: string): Promise<Book> {
  return get<Book>(`${API.BOOKS}/${encodeURIComponent(urn)}`);
}

export interface WorkListParams {
  category?: string;
  domain?: string;
  tradition?: string;
  canonical?: CanonicalRank;
  q?: string;
  sort?: WorkSort;
  limit?: number;
  offset?: number;
}

/** Volume-folded works for the Library: one entry per work, scoped by
    category, domain, and/or tradition, optionally narrowed to one canonical
    rank (the landmark rotations ask for primary_reference). */
export function getWorks(params: WorkListParams = {}): Promise<Page<Work>> {
  const qs = query({
    category: params.category ?? '',
    domain: params.domain ?? '',
    tradition: params.tradition ?? '',
    canonical: params.canonical ?? '',
    q: params.q ?? '',
    sort: params.sort ?? '',
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<Work>>(`${API.WORKS}${qs}`);
}

// ---- reader ----

export function getToc(urn: string): Promise<Toc> {
  return get<Toc>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.TOC}`);
}

/** Every volume of the work containing ``urn``, ascending by volume number:
    the reader's volume switcher. A single-volume work returns just itself. */
export function getBookVolumes(urn: string): Promise<Book[]> {
  return get<Book[]>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.VOLUMES}`);
}

export function getPage(urn: string, pageNumber: number): Promise<BookPage> {
  return get<BookPage>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.PAGES}/${pageNumber}`);
}

/** Verse-verified Qur'an citations located in a page's Arabic text: the
    auto-linkable set from the citation sidecar, each anchored by character
    offset so the reader can link the printed reference in place. */
export function getPageCitations(urn: string, pageNumber: number): Promise<QuranCitation[]> {
  const path = `${API.BOOKS}/${encodeURIComponent(urn)}${API.PAGES}/${pageNumber}${API.CITATIONS}`;
  return get<QuranCitation[]>(path);
}

export function searchBook(
  urn: string,
  q: string,
  limit?: number,
  offset?: number,
): Promise<Page<BookSearchMatch>> {
  const qs = query({ q, limit: limit ?? PAGE.defaultLimit, offset: offset ?? 0 });
  return get<Page<BookSearchMatch>>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.SEARCH}${qs}`);
}

// ---- search (one query, four scopes: works / content / narrator / quran) ----

export const SEARCH_SCOPES = ['content', 'works', 'narrator', 'quran'] as const;
export type SearchScope = (typeof SEARCH_SCOPES)[number];

/** The match modes in display order. `satisfies` locks every member to the
    served SearchMode union, so a backend rename or removal fails this line
    on the next types:gen instead of leaving a stale mode in the UI. */
export const SEARCH_MODES = ['exact', 'broad'] as const satisfies readonly SearchMode[];

/** True when `value` is a served match mode: the one validation point for
    mode strings arriving from outside the type system (the URL hash). */
export function isSearchMode(value: string): value is SearchMode {
  return (SEARCH_MODES as readonly string[]).includes(value);
}

export interface CorpusSearchParams {
  mode?: SearchMode;
  /** Category slugs to OR together (a UI domain pick arrives pre-expanded). */
  categories?: readonly string[];
  book?: string;
  volume?: number;
  limit?: number;
  offset?: number;
}

export function searchCorpus(
  q: string,
  params: CorpusSearchParams = {},
): Promise<Page<CorpusMatch>> {
  const qs = query({
    q,
    mode: params.mode ?? SEARCH.DEFAULT_MODE,
    category: params.categories ?? [],
    book: params.book ?? '',
    volume: params.volume ?? 0,
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<CorpusMatch>>(`${API.SEARCH}${qs}`);
}

export function searchFacets(
  q: string,
  mode: SearchMode = SEARCH.DEFAULT_MODE,
  categories: readonly string[] = [],
  book = '',
): Promise<SearchFacets> {
  const qs = query({ q, mode, category: categories, book });
  return get<SearchFacets>(`${API.SEARCH}${API.FACETS}${qs}`);
}

// ---- quran ----

/** Resolve a surah:ayah reference to its verse text (pointed + bare forms). */
export function getVerse(surah: number, ayah: number): Promise<Ayah> {
  return get<Ayah>(`${API.QURAN}/${surah}/${ayah}`);
}

/** Fetch a full surah: every numbered ayah in recitation order. */
export function getSurah(surah: number): Promise<Surah> {
  return get<Surah>(`${API.QURAN}/${surah}`);
}

/** Find Qurʾān verses whose text contains an Arabic term or phrase. */
export function searchQuran(
  q: string,
  params: { limit?: number; offset?: number } = {},
): Promise<Page<Ayah>> {
  const qs = query({ q, limit: params.limit ?? PAGE.defaultLimit, offset: params.offset ?? 0 });
  return get<Page<Ayah>>(`${API.QURAN}${API.SEARCH}${qs}`);
}

// ---- daily ----

export function getDaily(): Promise<Daily> {
  return get<Daily>(API.DAILY);
}

// ---- almanac ----

/** The full Hijri almanac; the client selects for its own "today" (hijri.ts). */
export function getAlmanac(): Promise<Almanac> {
  return get<Almanac>(API.ALMANAC);
}

// ---- narrator registries ----

export interface RijalParams {
  q?: string;
  tradition?: string;
  category?: string;
  has_teachers?: boolean;
  has_reliability?: boolean;
  limit?: number;
  offset?: number;
}

export function getRijal(params: RijalParams = {}): Promise<Page<RijalEntry>> {
  const qs = query({
    q: params.q ?? '',
    tradition: params.tradition ?? '',
    category: params.category ?? '',
    has_teachers: params.has_teachers ?? false,
    has_reliability: params.has_reliability ?? false,
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<RijalEntry>>(`${API.RIJAL}${qs}`);
}

export interface CanonicalParams {
  q?: string;
  merged_only?: boolean;
  limit?: number;
  offset?: number;
}

export function getCanonical(params: CanonicalParams = {}): Promise<Page<CanonicalEntry>> {
  const qs = query({
    q: params.q ?? '',
    merged_only: params.merged_only ?? false,
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<CanonicalEntry>>(`${API.CANONICAL}${qs}`);
}

/** Fetch one rijal entry by id — the reader's tarjama detail for a linked narrator. */
export function getRijalEntry(id: number): Promise<RijalEntry> {
  return get<RijalEntry>(`${API.RIJAL}/${id}`);
}

/** Fetch one canonical profile by id, for narrators linked to the canonical registry. */
export function getCanonicalEntry(id: number): Promise<CanonicalEntry> {
  return get<CanonicalEntry>(`${API.CANONICAL}/${id}`);
}
