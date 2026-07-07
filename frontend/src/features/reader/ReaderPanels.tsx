import { useState } from 'react';

import { Badge, IconButton, IsnadNode, Segmented } from '../../lib/design-system';
import type { Hadith, Narrator, NarratorRecord } from '../../lib/types';
import { joinDots } from '../../lib/utils';
import { reliabilityBadge } from '../../lib/variants';

const ISNAD_VIEWS = [
  { value: 'tree', label: 'Tree' },
  { value: 'flow', label: 'Flow' },
  { value: 'cards', label: 'Cards' },
];
type IsnadView = 'tree' | 'flow' | 'cards';

/** The right-hand isnād panel: the active unit's transmission chain in the
    reader's three layouts, every node opening its narrator. */
export function IsnadPanel({
  hadith,
  onNarrator,
}: {
  hadith: Hadith;
  onNarrator: (n: Narrator) => void;
}) {
  const [view, setView] = useState<IsnadView>('tree');
  return (
    <aside className="reader-isnad" aria-label="Isnād, transmission chain">
      <div className="reader-isnad__head">
        <p className="reader-isnad__label">Isnād · transmission chain</p>
        <p className="reader-isnad__sub">
          Hadith {hadith.n} · {hadith.narrators.length} narrators
          {hadith.grade ? ` · ${hadith.grade}` : ''}
        </p>
      </div>
      <div className="reader-isnad__views">
        <Segmented
          surface="reader"
          label="Isnād layout"
          value={view}
          options={ISNAD_VIEWS}
          onChange={(v) => setView(v as IsnadView)}
        />
      </div>
      {hadith.narrators.length === 0 ? (
        <p className="reader-isnad__empty">No transmission chain recorded for this unit.</p>
      ) : (
        <div className={`isnad-chain isnad-chain--${view}`}>
          {hadith.narrators.map((n, i) => (
            <IsnadNode
              key={i}
              variant={view === 'cards' ? 'card' : view === 'flow' ? 'flow' : 'tree'}
              index={i}
              showLine={view === 'tree' && i < hadith.narrators.length - 1}
              nameEn={n.name || n.name_ar}
              nameAr={n.name_ar}
              died={n.d}
              role={n.role}
              grade={n.grade}
              gradeVariant={reliabilityBadge(n.grade)}
              onClick={() => onNarrator(n)}
            />
          ))}
        </div>
      )}
    </aside>
  );
}

function narratorSource(record: NarratorRecord): string {
  if (record.id < 0) return 'Extracted from the text · no registry entry';
  return record.origin === 'person' ? 'Enriched person registry' : 'Rijāl registry';
}

export interface NarratorFetchError {
  id: number;
  origin: NarratorRecord['origin'];
  message: string;
}

/** The narrator biography panel (tarjama): name, grade, registry facts, and a
    loud inline error when the full biography fetch fails. */
export function TarjamaPanel({
  record,
  error,
  onClose,
}: {
  record: NarratorRecord;
  error: string | null;
  onClose: () => void;
}) {
  const sub = joinDots(record.kunya, record.nisba);
  const facts: [string, string | number][] = [
    ['Tradition', record.tradition || '—'],
    ['Died', record.death_year || '—'],
    ['Teachers', record.teacher_count],
    ['Students', record.student_count],
    ...(record.evaluator ? ([['Evaluator', record.evaluator]] as [string, string][]) : []),
    ['Source', record.source_label || '—'],
  ];
  return (
    <aside className="narrator" aria-label="Narrator biography">
      <div className="narrator__head">
        <p className="narrator__label">Tarjama · ترجمة</p>
        <IconButton surface="reader" size="sm" label="Close" icon="close" onClick={onClose} />
      </div>
      <p className="narrator__name" dir="rtl">
        {record.full_name}
      </p>
      {sub ? (
        <p className="narrator__sub" dir="rtl">
          {sub}
        </p>
      ) : null}
      {record.reliability_term ? (
        <div className="narrator__grade">
          <Badge surface="reader" variant={reliabilityBadge(record.reliability_term)} dir="rtl">
            {record.reliability_term}
          </Badge>
        </div>
      ) : null}
      <dl className="narrator__facts">
        {facts.map(([k, v]) => (
          <div key={k} className="narrator__fact">
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      {error ? (
        <p className="narrator__error" role="alert">
          Biography failed to load · {error}
        </p>
      ) : null}
      <p className="narrator__source">{narratorSource(record)}</p>
    </aside>
  );
}
