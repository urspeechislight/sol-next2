import { Highlight, IndexRow, Link, NewTabLink } from '../../lib/design-system';
import { readerHref } from '../../lib/routes';
import type { CorpusMatch } from '../../lib/types';
import { countLabel } from '../library/lib';
import { groupByWork, refLabel } from './passages';
import './PassageGroups.css';

export interface PassageGroupsProps {
  /** The full accumulated hit window, in server order. */
  items: readonly CorpusMatch[];
  q: string;
  /** The active book filter (stored Arabic title), '' when none. */
  activeBook: string;
  /** TRUE per-work passage counts (facet books within the chosen domain or
      category); empty at corpus scope, where the meta slot stays blank
      rather than dressing a window-local number as a total. */
  bookCounts: ReadonlyMap<string, number>;
  onPickBook: (title: string) => void;
  onOpen: (urn: string, page: number) => void;
}

/** The hit stream as an anthology, not a wall: hits arrive ordered by
    category -> book -> volume -> page, so each work becomes one contents row
    in the library's own IndexRow grammar: English title left with the author
    beneath it, dotted leader, mono meta, Arabic title on the spine side.
    Activating a head narrows the stream to that work (and releases it when
    pressed again); its meta carries exactly one meaning, the work's TRUE
    passage count when the facet scan provides it, else nothing. */
export function PassageGroups({
  items,
  q,
  activeBook,
  bookCounts,
  onPickBook,
  onOpen,
}: PassageGroupsProps) {
  const groups = groupByWork(items);
  return (
    <div className="pg">
      {groups.map((g) => {
        const on = g.title_ar === activeBook;
        const trueCount = bookCounts.get(g.title_ar);
        return (
          <section key={g.key} className="pg__group">
            <IndexRow
              en={g.title_en ?? ''}
              ar={g.title_ar}
              blurb={g.author}
              meta={trueCount !== undefined ? countLabel(trueCount, 'passage') : ''}
              current={on}
              onActivate={() => onPickBook(on ? '' : g.title_ar)}
              ariaLabel={
                on
                  ? `Stop filtering to ${g.title_en ?? g.title_ar}`
                  : `Show only passages from ${g.title_en ?? g.title_ar}`
              }
            />
            <div className="pg__rows">
              {g.hits.map((m, i) => (
                <PassageRow key={`${m.urn}-${m.page}-${i}`} m={m} q={q} onOpen={onOpen} />
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}

interface PassageRowProps {
  m: CorpusMatch;
  q: string;
  onOpen: (urn: string, page: number) => void;
}

/** One passage: the highlighted Arabic evidence leads at full width, the
    volume/page reference sits in a direction-isolated mono margin. The row
    is a real link to that reader position — a plain click drills in place,
    ctrl/cmd/middle-click opens a new tab exactly like any other link — plus
    an explicit NewTabLink for the same target, so previewing a hit never
    means losing this results page. The href carries the search term (q) so
    the reader highlights it even on a real navigation, not just in-place. */
function PassageRow({ m, q, onOpen }: PassageRowProps) {
  const href = readerHref(m.urn, m.page, q);
  const label = `${m.title_en ?? m.title_ar} at ${refLabel(m)}`;
  return (
    <div className="prow">
      <Link
        href={href}
        onActivate={() => onOpen(m.urn, m.page)}
        className="prow__link"
        ariaLabel={`Open ${label}`}
      >
        <span className="prow__ref" dir="ltr">
          {refLabel(m)}
        </span>
        <span className="prow__snip" dir="rtl" lang="ar">
          <Highlight text={m.snippet} query={q} />
        </span>
      </Link>
      <NewTabLink href={href} label={`Open ${label} in a new tab`} className="prow__newtab" />
    </div>
  );
}
