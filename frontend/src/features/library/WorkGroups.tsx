import { useState } from 'react';
import { UnstyledButton } from '../../lib/design-system';
import type { Work } from '../../lib/types';
import { WorkRecordList } from './WorkRecord';

export interface WorkGroup {
  key: string;
  labelEn: string;
  labelAr: string | null;
  /** Small mono annotation after the label, e.g. "d. 460 AH". */
  meta: string | null;
  works: Work[];
}

export interface WorkGroupsProps {
  groups: WorkGroup[];
  onOpen: (urn: string) => void;
}

/** Collapsed accordion of work groups (eras, authors): every group starts
    closed so a large scope reads as a table of contents, not a scroll. One
    click opens a group; several may stay open side by side. */
export function WorkGroups({ groups, onOpen }: WorkGroupsProps) {
  const [open, setOpen] = useState<Set<string>>(() => new Set());
  const toggle = (key: string) =>
    setOpen((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });

  return (
    <div className="wgroups">
      {groups.map((g) => {
        const isOpen = open.has(g.key);
        return (
          <section key={g.key} className={isOpen ? 'wgroup wgroup--open' : 'wgroup'}>
            <UnstyledButton
              className="wgroup__head"
              onClick={() => toggle(g.key)}
              ariaLabel={`${isOpen ? 'Collapse' : 'Expand'} ${g.labelEn}, ${g.works.length} works`}
              ariaPressed={isOpen}
            >
              <span className="wgroup__marker" aria-hidden="true">
                {isOpen ? '−' : '+'}
              </span>
              <span className="wgroup__en">{g.labelEn}</span>
              {g.labelAr ? (
                <span className="wgroup__ar" dir="rtl">
                  {g.labelAr}
                </span>
              ) : null}
              {g.meta ? <span className="wgroup__meta">{g.meta}</span> : null}
              <span className="wgroup__count">{g.works.length}</span>
            </UnstyledButton>
            {isOpen ? (
              <div className="wgroup__body">
                <WorkRecordList works={g.works} section={g.labelEn} onOpen={onOpen} />
              </div>
            ) : null}
          </section>
        );
      })}
    </div>
  );
}
