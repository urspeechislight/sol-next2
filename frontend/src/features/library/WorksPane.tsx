import { Heading, MetaBadges, Pager, SourceRecord, Spinner, Text } from '../../lib/design-system';
import type { Page, Work } from '../../lib/types';
import { DataView } from '../../lib/DataView';
import { deathLabel, pageCount } from '../../lib/utils';

interface WorkRecordProps {
  work: Work;
  section: string;
  onOpen: (urn: string) => void;
}

/** One work as the shared bilingual record, its meta carried by design-system
    badges (volume count, sect, death year, pages) on the English spine. Opening
    it opens the first volume in the reader. */
function WorkRecord({ work, section, onOpen }: WorkRecordProps) {
  return (
    <SourceRecord
      section={section}
      titleAr={work.title_ar}
      titleEn={work.title_en}
      author={work.author}
      authorAr={work.author_ar}
      badges={
        <MetaBadges
          volumeCount={work.volume_count}
          sect={work.sect}
          death={deathLabel(work.death_year_ah)}
          pageCount={work.page_count}
        />
      }
      onOpen={() => onOpen(work.first_urn)}
    />
  );
}

export interface WorksPaneProps {
  breadcrumb: string;
  scopeLabel: string;
  scopeLabelAr: string;
  works: Page<Work> | null;
  loading: boolean;
  error: Error | null;
  page: number;
  perPage: number;
  labelFor: (slug: string) => string;
  onPage: (page: number) => void;
  onOpen: (urn: string) => void;
}

/** The right pane for a chosen category, domain, or filter search: an Arabic-led
    header, a showing/total toolbar, the volume-folded work list, and a pager. */
export function WorksPane({
  breadcrumb,
  scopeLabel,
  scopeLabelAr,
  works,
  loading,
  error,
  page,
  perPage,
  labelFor,
  onPage,
  onOpen,
}: WorksPaneProps) {
  const total = works?.total ?? 0;
  const items = works?.items ?? [];
  const from = Math.min((page - 1) * perPage + 1, total);
  const to = Math.min(page * perPage, total);
  return (
    <section className="works">
      <header className="works__head">
        <Text size="xs" tone="faint" font="mono" className="works__crumb">
          {breadcrumb}
        </Text>
        <Heading level={2} font="arabic" dir="rtl">
          {scopeLabelAr}
        </Heading>
        <Text as="p" size="sm" tone="muted">
          {scopeLabel} · {total.toLocaleString()} works
        </Text>
      </header>
      <DataView
        result={{ data: works, error, loading }}
        errorText="Could not load works"
        renderLoading={() => (
          <div className="works__loading">
            <Spinner label="Loading works" />
          </div>
        )}
        isEmpty={(w) => w.items.length === 0}
        emptyText="No works in this scope."
      >
        {() => (
          <>
            <div className="works__toolbar">
              <Text size="xs" tone="faint" font="mono">
                {from.toLocaleString()}–{to.toLocaleString()} of {total.toLocaleString()}
              </Text>
            </div>
            <div className="ds-records">
              {items.map((w) => (
                <WorkRecord key={w.stem} work={w} section={labelFor(w.category)} onOpen={onOpen} />
              ))}
            </div>
            <Pager page={page} totalPages={pageCount(total, perPage)} onPage={onPage} />
          </>
        )}
      </DataView>
    </section>
  );
}
