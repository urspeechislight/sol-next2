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
  CanonicalRank,
  CorpusMatch,
  Daily,
  Domain,
  ExtractionBookSummary,
  ExtractionEntryAudit,
  ExtractionPage,
  HealthReport,
  Page,
  PersonEdge,
  PersonEntry,
  PersonGrade,
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

/** True when `err` is the API's 404 — the resource genuinely does not exist
    (book no longer served, page not yet ingested, dev tools disabled). The
    only status a caller may treat as "absent" and fall back on; every other
    failure is a transient fault that must surface as an error state. */
export function isNotFound(err: unknown): boolean {
  return err instanceof ApiError && err.status === 404;
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

// ---- health (the heartbeat polls this) ----

/** Probe every major subsystem; used by the 5-second heartbeat. */
export function getHealth(): Promise<HealthReport> {
  return get<HealthReport>(API.HEALTH);
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
  /** Resolve to the exact works containing these volume URNs, e.g. the
      distinct books behind a content-search hit window. */
  urns?: readonly string[];
  limit?: number;
  offset?: number;
}

/** Volume-folded works for the Library: one entry per work, scoped by
    category, domain, and/or tradition, optionally narrowed to one canonical
    rank (the landmark rotations ask for primary_reference), or resolved to
    an exact set of volume URNs (a content-search hit window's book set). */
export function getWorks(params: WorkListParams = {}): Promise<Page<Work>> {
  const qs = query({
    category: params.category ?? '',
    domain: params.domain ?? '',
    tradition: params.tradition ?? '',
    canonical: params.canonical ?? '',
    q: params.q ?? '',
    sort: params.sort ?? '',
    urn: params.urns ?? [],
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

// ---- search (one query, four global scopes plus the Qurʾān reader's own
// in-place "this sūra" filter over the currently open sūra) ----

export const SEARCH_SCOPES = ['content', 'works', 'narrator', 'quran', 'sura'] as const;
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

// ---- dev extraction inspection ----
// Served only when the backend opted in with SOL_DEV_TOOLS=true; otherwise
// these 404 and the extraction screen renders that state.

/** List the books in the manuscript artifact with extraction coverage. */
export function getExtractionBooks(): Promise<ExtractionBookSummary[]> {
  return get<ExtractionBookSummary[]>(`${API.DEV_EXTRACTION}${API.BOOKS}`);
}

/** One page's spans, units, and entities near-raw, for validation. */
export function getExtractionPage(urn: string, page: number): Promise<ExtractionPage> {
  return get<ExtractionPage>(
    `${API.DEV_EXTRACTION}${API.BOOKS}/${encodeURIComponent(urn)}${API.PAGES}/${page}`,
  );
}

/** Audit extracted units against the edition's printed entry numbers. */
export function getExtractionEntryAudit(urn: string): Promise<ExtractionEntryAudit> {
  return get<ExtractionEntryAudit>(
    `${API.DEV_EXTRACTION}${API.BOOKS}/${encodeURIComponent(urn)}${API.ENTRY_AUDIT}`,
  );
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

/** Fetch one rijal entry by id — the reader's tarjama detail for a linked narrator. */
export function getRijalEntry(id: number): Promise<RijalEntry> {
  return get<RijalEntry>(`${API.RIJAL}/${id}`);
}

export interface PersonParams {
  q?: string;
  tradition?: string;
  confidence?: string;
  has_events?: boolean;
  limit?: number;
  offset?: number;
}

/** List enriched narrator persons — the Graph browser's person registry. */
export function getPerson(params: PersonParams = {}): Promise<Page<PersonEntry>> {
  const qs = query({
    q: params.q ?? '',
    tradition: params.tradition ?? '',
    confidence: params.confidence ?? '',
    has_events: params.has_events ?? false,
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<PersonEntry>>(`${API.PERSON}${qs}`);
}

/** Fetch one enriched person by id — the reader's tarjama detail for a narrator. */
export function getPersonEntry(id: number): Promise<PersonEntry> {
  return get<PersonEntry>(`${API.PERSON}/${id}`);
}

/** A person's teacher/student relations, linked to a person id when known. */
export function getPersonEdges(id: number): Promise<PersonEdge[]> {
  return get<PersonEdge[]>(`${API.PERSON}/${id}/edges`);
}

/** A person's source-validated reliability grades, each with a relative reader deep-link. */
export function getPersonGrades(id: number): Promise<PersonGrade[]> {
  return get<PersonGrade[]>(`${API.PERSON}/${id}/grades`);
}
