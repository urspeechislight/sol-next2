import { useEffect, useState } from 'react';
import { Apparatus, Dots, NavArrow, UnstyledButton } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getToc, getWorks, isNotFound } from '../../lib/api/client';
import { PAGE } from '../../lib/constants';
import type { Work } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { deathLabel, joinDots, volumesLabel } from '../../lib/utils';
import { shelfOrder, shelfPolicy } from './shelf';
import './FoundationalShelf.css';

export interface FoundationalShelfProps {
  /** Scope: a domain id or a category slug. */
  domain?: string;
  category?: string;
  /** Tradition lens filter; '' keeps every tradition (only meaningful for the
      domain scope: a category carries one tradition by construction). */
  tradition?: string;
  onOpen: (urn: string, page?: number) => void;
}

interface ShelfData {
  works: Work[];
  total: number;
}

/** The foundational shelf as a hand-turned spotlight: the scope's primary
    references one at a time on the open shelf line, folio grammar, no card
    box, no invented cover, with arrows and dots that turn only by the
    reader's hand (unrequested motion is performance, not service). Renders
    nothing when the scope holds no primary references: the shelf never pads
    from the secondary tier. Opening a work lands on its first
    table-of-contents entry so the reader starts at content, not front
    matter. */
export function FoundationalShelf({ domain, category, tradition, onOpen }: FoundationalShelfProps) {
  const scope = category ?? domain ?? '';
  const res = useAsync<ShelfData>(
    () =>
      getWorks({
        domain,
        category,
        tradition,
        canonical: 'primary_reference',
        limit: PAGE.facetLimit,
      }).then((page) => ({ works: shelfOrder(page.items, shelfPolicy(scope)), total: page.total })),
    [domain, category, tradition, scope],
  );

  const works = res.data?.works ?? [];
  const [idx, setIdx] = useState(0);
  useEffect(() => setIdx(0), [works.length]);

  const work = works.length > 0 ? works[Math.min(idx, works.length - 1)] : null;
  const go = (delta: number) => setIdx((i) => (i + delta + works.length) % works.length);
  return (
    <DataView
      result={res}
      loadingLabel="Fetching the foundational works"
      errorText="Could not load the foundational works"
      isEmpty={(data) => data.works.length === 0}
      renderEmpty={() => null}
    >
      {() =>
        work ? (
          <section className="shelf" aria-label="Foundational works">
            <Apparatus marginalia={`${idx + 1} / ${works.length}`}>
              Foundational works · أمهات الكتب
            </Apparatus>
            <ShelfStage work={work} onOpen={onOpen} />
            {works.length > 1 ? (
              <footer className="shelf__foot">
                <NavArrow direction="back" label="Previous work" onClick={() => go(-1)} />
                <Dots
                  count={works.length}
                  active={idx}
                  labelFor={(i) => {
                    const w = works[i];
                    return w ? `Show ${w.title_en ?? w.title_ar}` : 'Show work';
                  }}
                  onPick={setIdx}
                />
                <NavArrow direction="forward" label="Next work" onClick={() => go(1)} />
              </footer>
            ) : null}
          </section>
        ) : null
      }
    </DataView>
  );
}

interface ShelfStageProps {
  work: Work;
  onOpen: (urn: string, page?: number) => void;
}

/** One work standing on the shelf line: the bilingual lockup at display
    scale, sliding in as the rotation turns. Falls back to the book's first
    page only when the work genuinely has no TOC (404 — page 1 is the default
    entry, not a guess); any other failure propagates rather than silently
    degrading. */
function ShelfStage({ work, onOpen }: ShelfStageProps) {
  const open = () => {
    void getToc(work.first_urn)
      .then((toc) => onOpen(work.first_urn, toc.entries[0]?.page))
      .catch((err: unknown) => {
        if (isNotFound(err)) return onOpen(work.first_urn);
        throw err;
      });
  };
  return (
    <div className="shelf__stage" key={work.stem}>
      <UnstyledButton
        className="shelf__work"
        onClick={open}
        ariaLabel={`Open ${work.title_en ?? work.title_ar}`}
      >
        <span className="shelf__ar" dir="rtl">
          {work.title_ar}
        </span>
        {work.title_en ? <span className="shelf__en">{work.title_en}</span> : null}
        <span className="shelf__author">{work.author ?? work.author_ar}</span>
        <span className="shelf__meta">
          {joinDots(deathLabel(work.death_year_ah), volumesLabel(work.volume_count))}
        </span>
        <span className="shelf__go">Open the book →</span>
      </UnstyledButton>
    </div>
  );
}
