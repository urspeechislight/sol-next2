import { Highlight, IndexRow, UnstyledButton } from '../../lib/design-system';
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
    volume/page reference sits in a direction-isolated mono margin, and the
    row opens the reader at the hit page. */
function PassageRow({ m, q, onOpen }: PassageRowProps) {
  return (
    <UnstyledButton
      className="prow"
      onClick={() => onOpen(m.urn, m.page)}
      ariaLabel={`Open ${m.title_en ?? m.title_ar} at ${refLabel(m)}`}
    >
      <span className="prow__ref" dir="ltr">
        {refLabel(m)}
      </span>
      <span className="prow__snip" dir="rtl" lang="ar">
        <Highlight text={m.snippet} query={q} />
      </span>
    </UnstyledButton>
  );
}
