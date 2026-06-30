import { useEffect, useState } from 'react';

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

/** Books by title/author/any. Has no server facet endpoint, so the category
    filter is derived from the returned rows (categoryFacets) and applied on the
    client, rendered through the same ResultsFrame as every other scope. */
function BooksScope({
  q,
  field,
  onOpenReader,
}: {
  q: string;
  field: BookField;
  onOpenReader: (urn: string) => void;
}) {
  const res = useAsync<Page<Book>>(
    () => searchBooks(q, { field, limit: PAGE.facetLimit }),
    [q, field],
  );
  const labelOf = useCategoryLabels();
  const [category, setCategory] = useState('');
  useEffect(() => setCategory(''), [q, field]);

  const items = res.data?.items ?? [];
  const slugOf = (b: Book) => b.category;
  const shown = byCategory(items, category, slugOf);
  const total = category ? shown.length : (res.data?.total ?? 0);
  const empty =
    res.data && shown.length === 0
      ? category
        ? 'No books in this category.'
        : `No books match “${q}”.`
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
      loadingLabel="Searching books"
      error={res.error ? `Book search is unavailable: ${res.error.message}` : null}
      empty={empty}
    >
      {res.data
        ? shown.map((b) => (
            <BookResult key={b.urn} b={b} section={labelOf(b.category)} onOpen={onOpenReader} />
          ))
        : null}
    </ResultsFrame>
  );
}

/** Narrators (rijāl). Same client-faceted frame as books, keyed on the entry's
    category, so the scope is the books pipeline with a different row + source. */
function NarratorsScope({ q }: { q: string }) {
  const res = useAsync<Page<RijalEntry>>(() => getRijal({ q, limit: PAGE.facetLimit }), [q]);
  const labelOf = useCategoryLabels();
  const [category, setCategory] = useState('');
  useEffect(() => setCategory(''), [q]);

  const items = res.data?.items ?? [];
  const slugOf = (e: RijalEntry) => e.category;
  const shown = byCategory(items, category, slugOf);
  const total = category ? shown.length : (res.data?.total ?? 0);
  const empty =
    res.data && shown.length === 0
      ? category
        ? 'No narrators in this category.'
        : `No narrators match “${q}”.`
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
      loadingLabel="Searching narrators"
      error={res.error ? `Narrator search is unavailable: ${res.error.message}` : null}
      empty={empty}
    >
      {res.data ? shown.map((e) => <NarratorCard key={e.id} item={e} />) : null}
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
        <BooksScope
          q={q}
          field={bookField(scope)}
          onOpenReader={(urn) => onOpenReader(urn, 1, '')}
        />
      ) : null}
      {scope === 'narrator' ? <NarratorsScope q={q} /> : null}
    </section>
  );
}
