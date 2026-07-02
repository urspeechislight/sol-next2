import { MetaBadges, SourceRecord } from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { deathLabel } from '../../lib/utils';

export interface WorkRecordProps {
  work: Work;
  section: string;
  onOpen: (urn: string) => void;
}

/** One work as the shared bilingual record, its meta carried by design-system
    badges (volume count, sect, death year, pages) on the English spine. Opening
    it opens the first volume in the reader. The single record renderer for
    every library listing (search, era groups, author groups, volume order). */
export function WorkRecord({ work, section, onOpen }: WorkRecordProps) {
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

export interface WorkRecordListProps {
  works: Work[];
  section: string;
  onOpen: (urn: string) => void;
}

/** A run of work records in the shared records container. */
export function WorkRecordList({ works, section, onOpen }: WorkRecordListProps) {
  return (
    <div className="ds-records">
      {works.map((w) => (
        <WorkRecord key={w.stem} work={w} section={section} onOpen={onOpen} />
      ))}
    </div>
  );
}
