import { Badge } from '../primitives/Badge';

export interface MetaBadgesProps {
  /** Shown as "N volumes" only when greater than 1 (folded multi-volume works). */
  volumeCount?: number | null;
  sect?: string | null;
  /** Pre-formatted death label, e.g. "d. 326 AH" (see deathLabel in utils). */
  death?: string;
  pageCount?: number | null;
}

/** The shared meta-badge row for a book or work: volume count, sect, death year,
    and page count rendered as design-system Badges. Used by book search and the
    library so the two surfaces never drift. */
export function MetaBadges({ volumeCount, sect, death, pageCount }: MetaBadgesProps) {
  return (
    <>
      {volumeCount && volumeCount > 1 ? <Badge>{volumeCount} volumes</Badge> : null}
      {sect ? <Badge>{sect}</Badge> : null}
      {death ? <Badge>{death}</Badge> : null}
      {pageCount ? <Badge>{pageCount.toLocaleString()} pp</Badge> : null}
    </>
  );
}
