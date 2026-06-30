import { useCallback, useEffect, useState } from 'react';

import { Badge, SourceRecord } from '../../lib/design-system';
import { searchCorpus, searchFacets } from '../../lib/api/client';
import type { SearchMode } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import type { CorpusMatch, Page, SearchFacets as Facets } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useCategoryLabels } from '../../lib/useCategoryLabels';
import { ResultsFrame } from './ResultsFrame';
import './SearchResults.css';

function PassageResult({
  m,
  section,
  q,
  onOpen,
}: {
  m: CorpusMatch;
  section: string;
  q: string;
  onOpen: (urn: string, page: number) => void;
}) {
  const reference = m.volume ? `vol. ${m.volume} · p. ${m.page}` : `p. ${m.page}`;
  return (
    <SourceRecord
      section={section}
      titleAr={m.title_ar}
      titleEn={m.title_en}
      author={m.author}
      badges={<Badge>{reference}</Badge>}
      snippet={m.snippet}
      query={q}
      onOpen={() => onOpen(m.urn, m.page)}
    />
  );
}

export interface ContentScopeProps {
  q: string;
  initialMode?: SearchMode;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

/** Full-text content search: exact/broad mode + category -> book -> volume
    drill-down, with highlighted passage results that open the reader. The
    Qurʾān scope reuses this with the resolved verse as `q` and `broad` as the
    initial mode, so full-verse and partial-verse quotations both surface. */
export function ContentScope({ q, initialMode = 'exact', onOpenReader }: ContentScopeProps) {
  const [mode, setMode] = useState<SearchMode>(initialMode);
  const [category, setCategory] = useState('');
  const [book, setBook] = useState('');
  const [volume, setVolume] = useState(0);

  const resetFilters = useCallback(() => {
    setCategory('');
    setBook('');
    setVolume(0);
  }, []);

  useEffect(() => resetFilters(), [q, resetFilters]);

  const corpus = useAsync<Page<CorpusMatch>>(
    () => searchCorpus(q, { mode, category, book, volume, limit: PAGE.defaultLimit }),
    [q, mode, category, book, volume],
  );
  const facetData = useAsync<Facets>(
    () => searchFacets(q, mode, category, book),
    [q, mode, category, book],
  );
  const labelOf = useCategoryLabels();

  const pickMode = (next: SearchMode) => {
    setMode(next);
    resetFilters();
  };
  const pickCategory = (slug: string) => {
    setCategory(slug);
    setBook('');
    setVolume(0);
  };
  const facets = facetData.data;
  const items = corpus.data?.items ?? [];
  const filtered = Boolean(category || book || volume);

  return (
    <ResultsFrame
      filters={{
        mode,
        categories: facets?.categories ?? [],
        books: facets?.books ?? [],
        volumes: facets?.volumes ?? [],
        labelOf,
        category,
        book,
        volume,
        total: corpus.data?.total ?? 0,
        onMode: pickMode,
        onCategory: pickCategory,
        onBook: (t) => {
          setBook(t);
          setVolume(0);
        },
        onVolume: setVolume,
        onClear: resetFilters,
      }}
      loading={corpus.loading}
      loadingLabel="Searching the corpus"
      error={corpus.error ? `Corpus search is unavailable: ${corpus.error.message}` : null}
      empty={
        corpus.data && items.length === 0
          ? filtered
            ? 'No passages match these filters.'
            : `No book passages match “${q}”.`
          : null
      }
    >
      {corpus.data
        ? items.map((m, i) => (
            <PassageResult
              key={`${m.urn}-${m.page}-${i}`}
              m={m}
              section={labelOf(m.category)}
              q={q}
              onOpen={(urn, page) => onOpenReader(urn, page, q)}
            />
          ))
        : null}
    </ResultsFrame>
  );
}
