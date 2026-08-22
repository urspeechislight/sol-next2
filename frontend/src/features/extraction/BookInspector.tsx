import { useEffect, useState } from 'react';

import { getExtractionEntryAudit, getExtractionPage } from '../../lib/api/client';
import { DataView } from '../../lib/DataView';
import { Button, Inline, Input, Stack, Text } from '../../lib/design-system';
import type { ExtractionBookSummary, ExtractionPage } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { clamp } from '../../lib/utils';
import { behaviorTone } from './behaviors';
import { SpanCard, UnitRow } from './SpanCard';

/** One book's coverage summary plus a page-by-page span browser. */
export function BookInspector({ book }: { book: ExtractionBookSummary }) {
  const [page, setPage] = useState(book.first_page);
  const result = useAsync(() => getExtractionPage(book.urn, page), [book.urn, page]);
  return (
    <Stack gap="md">
      <BookSummary book={book} />
      <EntryAudit urn={book.urn} />
      <InspectorPager page={page} last={book.page_end} onPage={(next) => setPage(clamp(next, 1, book.page_end))} />
      <DataView
        result={result}
        loadingLabel="Loading the page"
        errorText="Could not load this page"
        isEmpty={(data) => !data.spans.length && !data.units.length && !data.entities.length}
        emptyText={`Nothing starts on page ${page}. First extracted page: ${book.first_page}.`}
      >
        {(data) => <PageSpans data={data} />}
      </DataView>
    </Stack>
  );
}

/** Coverage numbers + the per-behavior unit distribution for the book. */
function BookSummary({ book }: { book: ExtractionBookSummary }) {
  return (
    <Stack gap="xs" className="xtr-book">
      <Inline gap="sm" align="center" wrap>
        <Text as="span" size="md" weight="semibold">
          {book.title_en ?? book.urn}
        </Text>
        <span className="xtr-mono">{book.urn}</span>
        <Text as="span" size="sm" tone="muted">
          {book.spans} spans · {book.units} units · {book.entities} entities ·{' '}
          {book.pages_with_spans} of {book.page_end} pages carry spans
        </Text>
      </Inline>
      <Inline gap="xs" wrap>
        {book.behaviors.map((count) => (
          <span
            key={count.behavior}
            className={`xtr-chip xtr-tone--${behaviorTone(count.behavior)}`}
          >
            {count.behavior}
            <span className="xtr-chip__n">{count.units}</span>
          </span>
        ))}
      </Inline>
    </Stack>
  );
}

/** The printed-ordinal sequence check: the edition's own numbering is ground
    truth, so per-section gaps and duplicates measure extraction completeness
    with no human reading. Clean sections stay summarized in the totals line;
    only anomalous sections get a detail row. */
function EntryAudit({ urn }: { urn: string }) {
  const result = useAsync(() => getExtractionEntryAudit(urn), [urn]);
  return (
    <DataView
      result={result}
      loadingLabel="Auditing entry numbers"
      errorText="Could not audit entry numbers"
      isEmpty={(audit) => audit.numbered_units === 0}
      emptyText="No units carry a printed entry number in this artifact."
    >
      {(audit) => {
        const anomalous = audit.rows.filter((row) => row.missing.length || row.duplicates.length);
        const broken = audit.missing_total + audit.duplicate_total > 0;
        return (
          <Stack gap="xs" className="xtr-audit">
            <Text as="p" size="sm" weight="semibold">
              Entry-number audit
            </Text>
            <Text as="p" size="sm" tone={broken ? 'danger' : 'muted'}>
              {audit.numbered_units} numbered units in {audit.sections} sections ·{' '}
              {audit.missing_total} missing · {audit.duplicate_total} duplicated ·{' '}
              {audit.sections_with_anomalies} sections affected
            </Text>
            {anomalous.map((row) => (
              <div key={row.section.join('|')} className="xtr-audit__row">
                <p className="xtr-crumb" dir="rtl" lang="ar">
                  {row.section.join(' ‹ ')}
                </p>
                <Text as="p" size="xs" tone="muted">
                  {row.first}..{row.last} · {row.units} units
                  {row.missing.length ? ` · missing ${row.missing.join(', ')}` : ''}
                  {row.duplicates.length ? ` · duplicated ${row.duplicates.join(', ')}` : ''}
                </Text>
              </div>
            ))}
          </Stack>
        );
      }}
    </DataView>
  );
}

interface InspectorPagerProps {
  page: number;
  last: number;
  onPage: (next: number) => void;
}

/** Prev/next plus a type-a-number jump; the jump commits on Enter. Named
    apart from the design-system's numeric-window Pager — a different
    interaction for an inspector, composed from the same primitives. */
function InspectorPager({ page, last, onPage }: InspectorPagerProps) {
  const [draft, setDraft] = useState(String(page));
  useEffect(() => setDraft(String(page)), [page]);
  const commit = () => {
    const parsed = Number(draft);
    if (Number.isFinite(parsed) && parsed >= 1) onPage(Math.trunc(parsed));
    else setDraft(String(page));
  };
  return (
    <Inline gap="sm" align="center" className="xtr-pager">
      <Button size="sm" variant="secondary" onClick={() => onPage(page - 1)}>
        Previous
      </Button>
      <span className="xtr-pager__jump">
        <Input value={draft} ariaLabel="Page number" onInput={setDraft} onSubmit={commit} />
        <Text as="span" size="sm" tone="muted">
          of {last}
        </Text>
      </span>
      <Button size="sm" variant="secondary" onClick={() => onPage(page + 1)}>
        Next
      </Button>
    </Inline>
  );
}

/** The page's spans with their units/entities joined back on; whatever is
    anchored to a span that started on an earlier page is listed separately
    rather than dropped. */
function PageSpans({ data }: { data: ExtractionPage }) {
  const spanIds = new Set(data.spans.map((span) => span.span_id));
  const orphanUnits = data.units.filter((unit) => !spanIds.has(unit.span_id));
  const orphanEntityCount = data.entities.filter((e) => !spanIds.has(e.span_id)).length;
  return (
    <Stack gap="md">
      {data.spans.map((span) => (
        <SpanCard
          key={span.span_id}
          span={span}
          units={data.units.filter((unit) => unit.span_id === span.span_id)}
          entities={data.entities.filter((entity) => entity.span_id === span.span_id)}
        />
      ))}
      {orphanUnits.length > 0 || orphanEntityCount > 0 ? (
        <Stack gap="xs" className="xtr-orphans">
          <Text as="p" size="sm" tone="muted">
            Anchored to spans that started on earlier pages
            {orphanEntityCount > 0 ? ` (plus ${orphanEntityCount} entities)` : ''}:
          </Text>
          {orphanUnits.map((unit) => (
            <UnitRow key={unit.unit_id} unit={unit} />
          ))}
        </Stack>
      ) : null}
    </Stack>
  );
}
