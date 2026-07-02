import { Badge, Eyebrow, ShareButton, Text, UnstyledButton } from '../../lib/design-system';
import { requestShare } from '../../lib/share';
import type { DailyHadith } from '../../lib/types';
import { hadithBadge } from '../../lib/variants';
import '../../components/HadithBlock.css';
import './HadithOfDay.css';

export interface HadithOfDayProps {
  hadith: DailyHadith;
  onOpenReader: (urn: string, page?: number) => void;
}

/** The folio's second voice, set as the verse's structural peer: open
    composition, isnād above the matn at display scale, translation and note
    beneath, and the citations as a labeled apparatus row. Every source and
    parallel the corpus holds opens the reader at the cited page; one it does
    not hold renders as a disabled pill, never a fabricated link. */
export function HadithOfDay({ hadith, onOpenReader }: HadithOfDayProps) {
  return (
    <article className="hday" aria-label="Hadith of the day">
      <header className="hday__head">
        <Eyebrow>Hadith of the day · حديث اليوم</Eyebrow>
        <Badge variant={hadithBadge(hadith.grade)} dot>
          <span dir="rtl">{hadith.grade_label}</span>
        </Badge>
      </header>

      {hadith.isnad_ar ? (
        <p className="hday__isnad" dir="rtl">
          {hadith.isnad_ar}
        </p>
      ) : null}

      <p className="hday__matn" dir="rtl">
        {hadith.matn_ar}
      </p>
      <p className="hday__en">{hadith.matn_en}</p>

      {hadith.note ? (
        <Text as="p" size="sm" tone="faint" className="hday__note">
          {hadith.note}
        </Text>
      ) : null}

      <div className="hday__refs">
        <div className="hday__refs-rule" aria-hidden="true">
          <span className="hday__refs-label">Read it in · اقرأه في</span>
        </div>
        <div className="hday__pills">
          <SourcePill
            bookAr={hadith.source.book_ar}
            n={hadith.source.n}
            urn={hadith.source.urn}
            page={hadith.source.page}
            onOpenReader={onOpenReader}
          />
          {hadith.parallels.map((p) => (
            <SourcePill
              key={`${p.book}-${p.n}`}
              bookAr={p.book_ar}
              n={p.n}
              urn={p.urn}
              page={p.page}
              onOpenReader={onOpenReader}
            />
          ))}
        </div>
      </div>

      <footer className="hday__foot">
        <ShareButton
          content={{
            kicker: `Hadith · ${hadith.source.book} № ${hadith.source.n}`,
            arabic: hadith.matn_ar,
            latin: hadith.matn_en,
            source: `${hadith.source.book} № ${hadith.source.n}`,
            url: window.location.origin,
          }}
          requestShare={requestShare}
        />
      </footer>
    </article>
  );
}

interface SourcePillProps {
  bookAr: string;
  n: string;
  urn: string | null;
  page: number | null;
  onOpenReader: (urn: string, page?: number) => void;
}

function SourcePill({ bookAr, n, urn, page, onOpenReader }: SourcePillProps) {
  return (
    <UnstyledButton
      className="hday__pill"
      onClick={() => (urn ? onOpenReader(urn, page ?? undefined) : undefined)}
      disabled={!urn}
      title={urn ? 'Open in the reader' : 'Not yet in the corpus'}
    >
      <span className="ref-pill">
        <span className="ref-pill__ar" dir="rtl">
          {bookAr}
        </span>
        <span className="ref-pill__pg">№ {n}</span>
      </span>
    </UnstyledButton>
  );
}
