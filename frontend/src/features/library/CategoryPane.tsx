import { useMemo, useState } from 'react';
import { Badge, Eyebrow, Segmented, Spinner, Text, UnstyledButton } from '../../lib/design-system';
import { LIBRARY } from '../../lib/constants';
import type { Work } from '../../lib/types';
import { deathLabel } from '../../lib/utils';
import { groupByAuthor, groupByEra, landmarks } from './lib';
import { ScopeHead } from './ScopeHead';
import type { WorkGroup } from './WorkGroups';
import { WorkGroups } from './WorkGroups';
import { WorkRecordList } from './WorkRecord';

type BrowseMode = 'era' | 'author' | 'volume';

const BROWSE_MODES = [
  { value: 'era', label: 'By era' },
  { value: 'author', label: 'By author' },
  { value: 'volume', label: 'By volumes' },
];

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
    then the whole scope as collapsed groups — by Hijri century, by author
    (most prolific first), or flat by volume count. Nothing scrolls endlessly:
    groups open on demand. */
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
  const [mode, setMode] = useState<BrowseMode>('era');
  const shelf = useMemo(() => (works ? landmarks(works) : []), [works]);
  const eraGroups = useMemo<WorkGroup[]>(
    () =>
      (works ? groupByEra(works) : []).map((e) => ({
        key: `era-${e.century}`,
        labelEn: e.labelEn,
        labelAr: e.labelAr,
        meta: null,
        works: e.works,
      })),
    [works],
  );
  const authorGroups = useMemo<WorkGroup[]>(
    () =>
      (works ? groupByAuthor(works) : []).map((a) => ({
        key: `author-${a.author}`,
        labelEn: a.author,
        labelAr: a.authorAr,
        meta: deathLabel(a.deathYearAh) || null,
        works: a.works,
      })),
    [works],
  );
  const byVolumes = useMemo(
    () =>
      [...(works ?? [])]
        .sort(
          (a, b) => b.volume_count - a.volume_count || (b.page_count ?? 0) - (a.page_count ?? 0),
        )
        .slice(0, LIBRARY.volumeViewMax),
    [works],
  );

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

  return (
    <section className="works cpane">
      <ScopeHead
        breadcrumb={breadcrumb}
        labelAr={scopeLabelAr}
        line={`${scopeLabel} · ${total.toLocaleString()} works`}
      />

      {shelf.length > 0 ? (
        <div className="cpane__shelf" aria-label="Landmark works">
          <Eyebrow className="cpane__shelf-label">Begin here · أمهات الكتب</Eyebrow>
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

      <div className="cpane__modes">
        <Segmented
          label="Browse the category"
          value={mode}
          options={BROWSE_MODES}
          onChange={(v) => setMode(v as BrowseMode)}
        />
      </div>

      {mode === 'era' ? <WorkGroups groups={eraGroups} onOpen={onOpen} /> : null}
      {mode === 'author' ? <WorkGroups groups={authorGroups} onOpen={onOpen} /> : null}
      {mode === 'volume' ? (
        <>
          <WorkRecordList works={byVolumes} section="Largest works" onOpen={onOpen} />
          {works.length > byVolumes.length ? (
            <Text as="p" size="xs" tone="faint" className="cpane__truncated">
              Showing the {byVolumes.length} largest of {works.length.toLocaleString()} works; the
              era and author views cover the rest.
            </Text>
          ) : null}
        </>
      ) : null}

      {works.length < total ? (
        <Text as="p" size="xs" tone="faint" className="cpane__truncated">
          Showing the first {works.length.toLocaleString()} of {total.toLocaleString()} works; use
          the search field to reach the rest.
        </Text>
      ) : null}
    </section>
  );
}
