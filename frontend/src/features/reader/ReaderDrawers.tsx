import { MatchRow, TocItem } from '../../lib/design-system';
import type { BookSearchMatch, Toc } from '../../lib/types';

export function TocDrawer({
  toc,
  current,
  onJump,
}: {
  toc: Toc;
  current: number;
  onJump: (page: number) => void;
}) {
  // The current section is the last entry that begins at or before the current
  // page — the same rule the backend uses for the page's chapter title. Mark
  // only that one row current; several sections can share a page number, and
  // matching on page alone lit every one of them.
  let currentIndex = -1;
  toc.entries.forEach((t, i) => {
    if (t.page <= current) currentIndex = i;
  });
  return (
    <aside className="reader-toc" aria-label="Table of contents">
      <p className="reader-toc__label">Contents</p>
      {toc.entries.map((t, i) => (
        <TocItem
          key={`${t.page}-${t.title}-${i}`}
          titleAr={t.title}
          titleEn={t.title_en}
          page={t.page}
          current={i === currentIndex}
          onClick={() => onJump(t.page)}
        />
      ))}
    </aside>
  );
}

interface MatchListProps {
  query: string;
  results: BookSearchMatch[];
  total: number;
  loading: boolean;
  onJump: (page: number) => void;
}

/** The in-book search results, shown in the left drawer whenever a query is
    active. The query field itself lives in the reader toolbar; this panel only
    lists the result rows. The diacritic-insensitive highlighting is the
    MatchRow's, unchanged from when the field sat here. */
export function MatchList({ query, results, total, loading, onJump }: MatchListProps) {
  return (
    <aside className="reader-toc" aria-label="In-book search">
      <p className="reader-toc__label">Search in book{total ? ` · ${total}` : ''}</p>
      <p className="reader-search__hint">Arabic queries are matched diacritic-insensitively.</p>
      {loading ? <p className="reader-search__hint">Searching…</p> : null}
      {!loading && results.length === 0 ? <p className="reader-search__hint">No matches.</p> : null}
      {results.map((m, i) => (
        <MatchRow
          key={`${m.page}-${i}`}
          page={m.page}
          snippet={m.snippet}
          query={query}
          onClick={() => onJump(m.page)}
        />
      ))}
    </aside>
  );
}
