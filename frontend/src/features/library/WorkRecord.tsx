import { UnstyledButton } from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { deathLabel, joinDots, volumesLabel } from '../../lib/utils';
import './WorkRecord.css';

export interface WorkRecordProps {
  work: Work;
  /** Optional context annotation (e.g. the category label in search results). */
  section?: string;
  onOpen: (urn: string) => void;
}

/** One work as a compact catalog row: English title and author as the reading
    voice, dotted leader, mono meta in a consistent right margin (volumes,
    death year, a gold mark for foundational works), Arabic title on the spine
    side. The single row renderer for every library listing. */
export function WorkRecord({ work, section, onOpen }: WorkRecordProps) {
  const meta = joinDots(volumesLabel(work.volume_count), deathLabel(work.death_year_ah), section);
  return (
    <UnstyledButton
      className="wrow"
      onClick={() => onOpen(work.first_urn)}
      ariaLabel={`Open ${work.title_en ?? work.title_ar}`}
    >
      <span className="wrow__main">
        {work.canonical === 'primary_reference' ? (
          <span className="wrow__mark" title="Foundational work" aria-hidden="true">
            ✻
          </span>
        ) : null}
        <span className="wrow__en">{work.title_en ?? work.title_ar}</span>
        {work.author ? <span className="wrow__author">{work.author}</span> : null}
      </span>
      <span className="wrow__leader" aria-hidden="true" />
      <span className="wrow__meta">{meta}</span>
      <span className="wrow__ar" dir="rtl">
        {work.title_ar}
      </span>
    </UnstyledButton>
  );
}
