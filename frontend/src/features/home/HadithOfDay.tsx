import { Badge, ShareButton, Text, UnstyledButton } from '../../lib/design-system';
import { requestShare } from '../../lib/share';
import type { DailyHadith } from '../../lib/types';
import { hadithBadge } from '../../lib/variants';
import '../../components/HadithBlock.css';
import './HadithOfDay.css';

export interface HadithOfDayProps {
  hadith: DailyHadith;
  onOpenReader: (urn: string) => void;
}

/** The landing hadith: isnād set apart above a hairline, matn beneath it in
    both languages, the grading on the head row, and every source and parallel
    a pill that opens the reader at that book. */
export function HadithOfDay({ hadith, onOpenReader }: HadithOfDayProps) {
  return (
    <section className="hday" aria-label="Hadith of the day">
      <header className="hday__head">
        <Text size="xs" tone="accent" weight="semibold" className="hday__eyebrow">
          Hadith of the day · حديث اليوم
        </Text>
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
        <Text as="p" size="sm" tone="muted" className="hday__note">
          {hadith.note}
        </Text>
      ) : null}

      <div className="hday__sources">
        <span className="hadith__refs-label">Read it in</span>
        <SourcePill
          bookAr={hadith.source.book_ar}
          n={hadith.source.n}
          urn={hadith.source.urn}
          onOpenReader={onOpenReader}
        />
        {hadith.parallels.map((p) => (
          <SourcePill
            key={`${p.book}-${p.n}`}
            bookAr={p.book_ar}
            n={p.n}
            urn={p.urn}
            onOpenReader={onOpenReader}
          />
        ))}
        <span className="hday__share">
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
        </span>
      </div>
    </section>
  );
}

interface SourcePillProps {
  bookAr: string;
  n: string;
  urn: string | null;
  onOpenReader: (urn: string) => void;
}

function SourcePill({ bookAr, n, urn, onOpenReader }: SourcePillProps) {
  return (
    <UnstyledButton
      className="hday__pill"
      onClick={() => (urn ? onOpenReader(urn) : undefined)}
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
