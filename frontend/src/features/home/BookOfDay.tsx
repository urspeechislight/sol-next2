import { Button, Eyebrow } from '../../lib/design-system';
import { DataView } from '../../lib/DataView';
import { getBook } from '../../lib/api/client';
import type { Book, DailyBookPick } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { deathLabel, joinDots } from '../../lib/utils';
import './BookOfDay.css';

export interface BookOfDayProps {
  pick: DailyBookPick;
  onOpenReader: (urn: string, page?: number) => void;
}

/** The book of the day: a full-width shelf band beneath the daily spread.
    The pick (URN, rationale, opening anchor) comes from the daily rotation;
    title and author resolve from the catalogue so the card can never
    disagree with the library. */
export function BookOfDay({ pick, onOpenReader }: BookOfDayProps) {
  const book = useAsync<Book>(() => getBook(pick.urn), [pick.urn]);
  return (
    <article className="bday" aria-label="Book of the day">
      <header className="bday__head">
        <Eyebrow>Book of the day · كتاب اليوم</Eyebrow>
      </header>
      <DataView result={book} loadingLabel="Fetching the book" errorText="Could not load the book">
        {(data) => (
          <div className="bday__body">
            <div className="bday__lockup">
              <h3 className="bday__title" dir="rtl">
                {data.title_ar}
              </h3>
              {data.title_en ? <p className="bday__title-en">{data.title_en}</p> : null}
              <p className="bday__author">
                {joinDots(data.author ?? data.author_ar, deathLabel(data.death_year_ah))}
              </p>
            </div>
            <blockquote className="bday__reason">{pick.rationale}</blockquote>
            <div className="bday__open">
              <Button
                variant="secondary"
                size="sm"
                iconBefore="book"
                onClick={() => onOpenReader(pick.urn, pick.open_to.page)}
              >
                Open at {pick.open_to.chapter_en}
              </Button>
            </div>
          </div>
        )}
      </DataView>
    </article>
  );
}
