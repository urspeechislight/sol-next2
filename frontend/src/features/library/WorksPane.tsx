import { Pager, Spinner, Text } from '../../lib/design-system';
import type { Page, Work } from '../../lib/types';
import { DataView } from '../../lib/DataView';
import { pageCount } from '../../lib/utils';
import { ScopeHead } from './ScopeHead';
import { WorkRecord } from './WorkRecord';

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
  return (
    <section className="works">
      <ScopeHead
        breadcrumb={breadcrumb}
        labelAr={scopeLabelAr}
        line={`${scopeLabel} · ${total.toLocaleString()} works`}
      />
      <DataView
        result={{ data: works, error, loading }}
        errorText="Could not load works"
        renderLoading={() => (
          <div className="library__loading">
            <Spinner label="Loading works" />
          </div>
        )}
        isEmpty={(w) => w.items.length === 0}
        emptyText="No works in this scope."
      >
        {(data) => {
          const from = Math.min((page - 1) * perPage + 1, data.total);
          const to = Math.min(page * perPage, data.total);
          return (
            <>
              <div className="works__toolbar">
                <Text size="xs" tone="faint" font="mono">
                  {from.toLocaleString()}–{to.toLocaleString()} of {data.total.toLocaleString()}
                </Text>
              </div>
              <div className="ds-records">
                {data.items.map((w) => (
                  <WorkRecord key={w.stem} work={w} section={labelFor(w.category)} onOpen={onOpen} />
                ))}
              </div>
              <Pager page={page} totalPages={pageCount(data.total, perPage)} onPage={onPage} />
            </>
          );
        }}
      </DataView>
    </section>
  );
}
