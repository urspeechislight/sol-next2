import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';

import { Heading, MetaBadges, SourceRecord, Text } from '../../lib/design-system';
import { getRijal, searchBooks } from '../../lib/api/client';
import type { BookSearchParams, SearchScope } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import { byCategory, categoryFacets } from '../../lib/facets';
import type { Book, Page, RijalEntry } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useCategoryLabels } from '../../lib/useCategoryLabels';
import { deathLabel } from '../../lib/utils';
import { NarratorCard } from '../narrators/NarratorCard';
import { ContentScope } from './ContentScope';
import { QuranScope } from './QuranScope';
import { ResultsFrame } from './ResultsFrame';
import '../screens.css';
import './SearchResults.css';

type BookField = NonNullable<BookSearchParams['field']>;

function bookField(scope: SearchScope): BookField {
  if (scope === 'title') return 'title';
  if (scope === 'author') return 'author';
  return 'any';
}

function BookResult({
  b,
  section,
  onOpen,
}: {
  b: Book;
  section: string;
  onOpen: (urn: string) => void;
}) {
  return (
    <SourceRecord
      section={section}
      titleAr={b.title_ar}
      titleEn={b.title_en}
      author={b.author}
      authorAr={b.author_ar}
      badges={
        <MetaBadges sect={b.sect} death={deathLabel(b.death_year_ah)} pageCount={b.page_count} />
      }
      onOpen={() => onOpen(b.urn)}
    />
  );
}

interface FacetedScopeProps<T> {
  q: string;
  /** Fetch/reset dependencies; the category filter clears when any changes. */
  deps: readonly unknown[];
  fetchPage: () => Promise<Page<T>>;
  slugOf: (item: T) => string;
  /** Lowercase plural for messages, e.g. "books" -> "No books match …". */
  noun: string;
  /** Capitalized singular for the error line, e.g. "Book" -> "Book search is unavailable". */
  kind: string;
  renderRow: (item: T, labelOf: (slug: string) => string) => ReactNode;
}

/** A search scope without a server facet endpoint: fetch one page, derive the
    category filter from the returned rows (categoryFacets), apply it on the
    client, and render through the shared ResultsFrame. Books and narrators are
    this one pipeline with a different fetch, row, and noun. */
function FacetedScope<T>({ q, deps, fetchPage, slugOf, noun, kind, renderRow }: FacetedScopeProps<T>) {
  const res = useAsync<Page<T>>(fetchPage, deps);
  const labelOf = useCategoryLabels();
  const [category, setCategory] = useState('');
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => setCategory(''), deps);

  const items = res.data?.items ?? [];
  const shown = byCategory(items, category, slugOf);
  const total = category ? shown.length : (res.data?.total ?? 0);
  const empty =
    res.data && shown.length === 0
      ? category
        ? `No ${noun} in this category.`
        : `No ${noun} match “${q}”.`
      : null;

  return (
    <ResultsFrame
      filters={{
        categories: categoryFacets(items, slugOf),
        labelOf,
        category,
        total,
        onCategory: setCategory,
        onClear: () => setCategory(''),
      }}
      loading={res.loading}
      loadingLabel={`Searching ${noun}`}
      error={res.error ? `${kind} search is unavailable: ${res.error.message}` : null}
      empty={empty}
    >
      {res.data ? shown.map((item) => renderRow(item, labelOf)) : null}
    </ResultsFrame>
  );
}

export interface SearchResultsProps {
  query: string;
  scope: SearchScope;
  /** Launch a new search from a result, e.g. a Qurʾān verse opens its reference. */
  onSearch: (q: string, scope: SearchScope) => void;
  onOpenReader: (urn: string, page: number, query: string) => void;
}

export function SearchResults({ query, scope, onSearch, onOpenReader }: SearchResultsProps) {
  const q = query.trim();
  const isBook = scope === 'title' || scope === 'author' || scope === 'book';
  const field = bookField(scope);
  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">
          Search · بحث
        </Text>
        <Heading level={1}>Results for “{q}”</Heading>
      </header>
      {scope === 'content' ? <ContentScope q={q} onOpenReader={onOpenReader} /> : null}
      {scope === 'quran' ? (
        <QuranScope q={q} onSearch={onSearch} onOpenReader={onOpenReader} />
      ) : null}
      {isBook ? (
        <FacetedScope<Book>
          q={q}
          deps={[q, field]}
          fetchPage={() => searchBooks(q, { field, limit: PAGE.facetLimit })}
          slugOf={(b) => b.category}
          noun="books"
          kind="Book"
          renderRow={(b, labelOf) => (
            <BookResult
              key={b.urn}
              b={b}
              section={labelOf(b.category)}
              onOpen={(urn) => onOpenReader(urn, 1, '')}
            />
          )}
        />
      ) : null}
      {scope === 'narrator' ? (
        <FacetedScope<RijalEntry>
          q={q}
          deps={[q]}
          fetchPage={() => getRijal({ q, limit: PAGE.facetLimit })}
          slugOf={(e) => e.category}
          noun="narrators"
          kind="Narrator"
          renderRow={(e) => <NarratorCard key={e.id} item={e} />}
        />
      ) : null}
    </section>
  );
}
