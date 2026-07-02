// client.ts:the only data path to the :8001 backend (proxied via vite /api).
// Every call is a GET; failures throw ApiError (fail loud, no silent fallback)
// so callers render an explicit error state. CENTRAL-007 confines fetch here.
import { PAGE } from '../constants';
import { API } from '../routes';
import type {
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
  RijalEntry,
  SearchFacets,
  Surah,
  Toc,
  Work,
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

type QueryValue = string | number | boolean;

async function get<T>(path: string): Promise<T> {
  const url = `${API.BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, url);
  return (await res.json()) as T;
}

/** Build a query string, dropping empty strings and false flags. */
function query(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === '' || value === false) continue;
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
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<Work>>(`${API.WORKS}${qs}`);
}

// ---- reader ----

export function getToc(urn: string): Promise<Toc> {
  return get<Toc>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.TOC}`);
}

export function getPage(urn: string, pageNumber: number): Promise<BookPage> {
  return get<BookPage>(`${API.BOOKS}/${encodeURIComponent(urn)}${API.PAGES}/${pageNumber}`);
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

// ---- search (one query, many scopes: content / title / author / book / narrator) ----

export const SEARCH_SCOPES = ['content', 'title', 'author', 'book', 'narrator', 'quran'] as const;
export type SearchScope = (typeof SEARCH_SCOPES)[number];
export type SearchMode = 'exact' | 'broad';

export interface CorpusSearchParams {
  mode?: SearchMode;
  category?: string;
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
    mode: params.mode ?? 'exact',
    category: params.category ?? '',
    book: params.book ?? '',
    volume: params.volume ?? 0,
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<CorpusMatch>>(`${API.SEARCH}${qs}`);
}

export function searchFacets(
  q: string,
  mode: SearchMode = 'exact',
  category = '',
  book = '',
): Promise<SearchFacets> {
  const qs = query({ q, mode, category, book });
  return get<SearchFacets>(`${API.SEARCH}${API.FACETS}${qs}`);
}

export interface BookSearchParams {
  field?: 'title' | 'author' | 'any';
  limit?: number;
  offset?: number;
}

export function searchBooks(q: string, params: BookSearchParams = {}): Promise<Page<Book>> {
  const qs = query({
    q,
    field: params.field ?? 'any',
    limit: params.limit ?? PAGE.defaultLimit,
    offset: params.offset ?? 0,
  });
  return get<Page<Book>>(`${API.SEARCH}${API.BOOKS}${qs}`);
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
