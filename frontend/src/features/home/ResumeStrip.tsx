import { useEffect, useMemo } from 'react';
import { UnstyledButton } from '../../lib/design-system';
import { getBook, isNotFound } from '../../lib/api/client';
import { clearReading, lastReading } from '../../lib/reading';
import type { Book } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import './ResumeStrip.css';

export interface ResumeStripProps {
  onOpenReader: (urn: string, page?: number) => void;
}

/** The re-entry path: when localStorage remembers a reading position, one
    slim bar above the folio resumes it in a tap. Absent for first-timers.
    A position whose book the catalogue no longer serves (404) is stale local
    state: it is cleared, and the strip simply does not render. Any other
    failure is transient — the position is kept, and this load renders
    nothing rather than wiping it. */
export function ResumeStrip({ onOpenReader }: ResumeStripProps) {
  const position = useMemo(() => lastReading(), []);
  const book = useAsync<Book | null>(
    () => (position ? getBook(position.urn) : Promise.resolve(null)),
    [position ? position.urn : ''],
  );

  useEffect(() => {
    if (book.error && isNotFound(book.error)) clearReading();
  }, [book.error]);

  if (!position || !book.data) return null;
  return (
    <UnstyledButton
      className="resume"
      onClick={() => onOpenReader(position.urn, position.page)}
      title="Return to where you left off"
    >
      <span className="resume__label">Continue reading · واصل القراءة</span>
      <span className="resume__title" dir="rtl">
        {book.data.title_ar}
      </span>
      {book.data.title_en ? <span className="resume__title-en">{book.data.title_en}</span> : null}
      <span className="resume__page">
        page {position.page}
        {book.data.page_count ? ` of ${book.data.page_count}` : ''}
      </span>
      <span className="resume__go" aria-hidden="true">
        →
      </span>
    </UnstyledButton>
  );
}
