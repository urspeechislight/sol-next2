// client.ts:the only data path. Real sol-next endpoints, fail loud, no fallback.
// Stage-2 reconciliation: import depth corrected (../constants, ../types:this
// file lives in lib/api/); API now comes from routes.ts (CENTRAL-006 split); and
// the paginated getters annotate params as `number` so the `as const` PAGE
// defaults don't narrow them to literal types (breaks the collect() signature).
import { PAGE } from '../constants';
import { API } from '../routes';
import type {
  BookData,
  BookGenre,
  CanonicalEntry,
  HistoryEntry,
  NarratorRecord,
  Paginated,
  ReaderPage,
  RijalEntry,
} from '../types';
import { canonicalToRecord, mergeNarrators, rijalToRecord } from '../narrators';

export class ApiError extends Error {
  status: number;
  url: string;
  constructor(status: number, url: string) {
    super(`API ${status}: ${url}`);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
  }
}

async function get<T>(path: string): Promise<T> {
  const url = `${API.BASE}${path}`;
  const res = await fetch(url);
  if (!res.ok) throw new ApiError(res.status, url);
  return (await res.json()) as T;
}

function paged(path: string, page: number, perPage: number): string {
  return `${path}?page=${page}&per_page=${perPage}`;
}

export function getRijal(
  page: number = PAGE.defaultPage,
  perPage: number = PAGE.defaultPerPage,
): Promise<Paginated<RijalEntry>> {
  return get<Paginated<RijalEntry>>(paged(API.RIJAL, page, perPage));
}

export function getCanonical(
  page: number = PAGE.defaultPage,
  perPage: number = PAGE.defaultPerPage,
): Promise<Paginated<CanonicalEntry>> {
  return get<Paginated<CanonicalEntry>>(paged(API.CANONICAL, page, perPage));
}

export function getHistory(
  page: number = PAGE.defaultPage,
  perPage: number = PAGE.defaultPerPage,
): Promise<Paginated<HistoryEntry>> {
  return get<Paginated<HistoryEntry>>(paged(API.HISTORY, page, perPage));
}

export function getCatalog(): Promise<BookGenre[]> {
  return get<BookGenre[]>(API.BOOKS);
}

export function getBook(slug: string): Promise<BookData> {
  return get<BookData>(`${API.DATA}/${encodeURIComponent(slug)}`);
}

export function getPage(slug: string, pageNumber: number): Promise<ReaderPage> {
  return get<ReaderPage>(`${API.BOOKS}/${encodeURIComponent(slug)}${API.PAGE}/${pageNumber}`);
}

async function collect<T>(
  fetcher: (page: number, perPage: number) => Promise<Paginated<T>>,
  maxPages: number,
  perPage: number,
): Promise<T[]> {
  const out: T[] = [];
  let page = 1;
  let totalPages = 1;
  do {
    const res = await fetcher(page, perPage);
    totalPages = res.total_pages;
    out.push(...res.entries);
    page += 1;
  } while (page <= totalPages && page <= maxPages);
  return out;
}

/** Build the narrator index for in-reader tarjama: rijal (with reliability) +
    canonical, merged by name. Paged + capped to stay light. */
export async function getNarratorIndex(maxPages = 6, perPage = 100): Promise<NarratorRecord[]> {
  const [rijal, canonical] = await Promise.all([
    collect<RijalEntry>(getRijal, maxPages, perPage),
    collect<CanonicalEntry>(getCanonical, maxPages, perPage),
  ]);
  return mergeNarrators(rijal.map(rijalToRecord), canonical.map(canonicalToRecord));
}
