import { useMemo } from 'react';
import {
  Badge,
  Heading,
  MetaBadges,
  SourceRecord,
  Spinner,
  Text,
  UnstyledButton,
} from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { deathLabel } from '../../lib/utils';
import { groupByEra, landmarks } from './lib';
import { ScopeHead } from './ScopeHead';

export interface CategoryPaneProps {
  breadcrumb: string;
  scopeLabel: string;
  scopeLabelAr: string;
  works: Work[] | null;
  total: number;
  loading: boolean;
  error: Error | null;
  onOpen: (urn: string) => void;
}

/** A category reads as a curated room: the landmark references shelved first,
    then every work grouped by Hijri century with era chips to jump. No pager,
    no flat dump; the era structure is the navigation. */
export function CategoryPane({
  breadcrumb,
  scopeLabel,
  scopeLabelAr,
  works,
  total,
  loading,
  error,
  onOpen,
}: CategoryPaneProps) {
  const shelf = useMemo(() => (works ? landmarks(works) : []), [works]);
  const eras = useMemo(() => (works ? groupByEra(works) : []), [works]);

  if (loading) {
    return (
      <div className="library__loading">
        <Spinner label="Loading the category" />
      </div>
    );
  }
  if (error || !works) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load works{error ? `: ${error.message}` : ''}.
      </Text>
    );
  }

  const jumpTo = (century: number) =>
    document.getElementById(`era-${century}`)?.scrollIntoView({ behavior: 'smooth' });

  return (
    <section className="works cpane">
      <ScopeHead
        breadcrumb={breadcrumb}
        labelAr={scopeLabelAr}
        line={`${scopeLabel} · ${total.toLocaleString()} works`}
      />

      {shelf.length > 0 ? (
        <div className="cpane__shelf" aria-label="Landmark works">
          <Text size="xs" tone="accent" weight="semibold" className="cpane__shelf-label">
            Begin here · أمهات الكتب
          </Text>
          <div className="cpane__shelf-row">
            {shelf.map((w) => (
              <UnstyledButton
                key={w.stem}
                className="cpane__landmark"
                onClick={() => onOpen(w.first_urn)}
                ariaLabel={`Open ${w.title_en ?? w.title_ar}`}
              >
                <span className="cpane__landmark-ar" dir="rtl">
                  {w.title_ar}
                </span>
                {w.title_en ? <span className="cpane__landmark-en">{w.title_en}</span> : null}
                {w.author ? <span className="cpane__landmark-author">{w.author}</span> : null}
                <span className="cpane__landmark-meta">
                  {deathLabel(w.death_year_ah) ? (
                    <Badge>{deathLabel(w.death_year_ah)}</Badge>
                  ) : null}
                  <Badge variant="success">Primary reference</Badge>
                </span>
              </UnstyledButton>
            ))}
          </div>
        </div>
      ) : null}

      {eras.length > 1 ? (
        <nav className="cpane__eras" aria-label="Jump to century">
          {eras.map((e) => (
            <UnstyledButton
              key={e.century}
              className="cpane__era-chip"
              onClick={() => jumpTo(e.century)}
            >
              {e.labelEn.replace(' century AH', ' c.')} · {e.works.length}
            </UnstyledButton>
          ))}
        </nav>
      ) : null}

      {eras.map((e) => (
        <section key={e.century} id={`era-${e.century}`} className="cpane__era">
          <header className="cpane__era-head">
            <Heading level={3} className="cpane__era-en">
              {e.labelEn}
            </Heading>
            <span className="cpane__era-ar" dir="rtl">
              {e.labelAr}
            </span>
            <span className="cpane__era-n">{e.works.length}</span>
          </header>
          <div className="ds-records">
            {e.works.map((w) => (
              <SourceRecord
                key={w.stem}
                section={e.labelEn}
                titleAr={w.title_ar}
                titleEn={w.title_en}
                author={w.author}
                authorAr={w.author_ar}
                badges={
                  <MetaBadges
                    volumeCount={w.volume_count}
                    sect={w.sect}
                    death={deathLabel(w.death_year_ah)}
                    pageCount={w.page_count}
                  />
                }
                onOpen={() => onOpen(w.first_urn)}
              />
            ))}
          </div>
        </section>
      ))}

      {works.length < total ? (
        <Text as="p" size="xs" tone="faint" className="cpane__truncated">
          Showing the first {works.length.toLocaleString()} of {total.toLocaleString()} works; use
          the search field to reach the rest.
        </Text>
      ) : null}
    </section>
  );
}
