import { Badge, Button, Card, Divider, Heading, ShareButton, Spinner, Text } from '../../lib/design-system';
import { getDaily } from '../../lib/api/client';
import { requestShare } from '../../lib/share';
import type { Daily, DailyHadith, Verse } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { reliabilityBadge } from '../../lib/variants';
import '../screens.css';
import './DailyScreen.css';

function VerseCard({ verse }: { verse: Verse }) {
  const tafsir = verse.tafsirs[0];
  return (
    <Card variant="flat" pad="lg">
      <Text size="xs" tone="faint" weight="semibold" className="daily__label">
        Qurʾān · {verse.surah} {verse.surah_n}:{verse.ayah_n}
      </Text>
      <p className="daily__ayah" dir="rtl">
        {verse.ayah_ar}
      </p>
      <p className="daily__ayah-en">
        <Text size="md" tone="muted" font="serif">
          {verse.ayah_en}
        </Text>
      </p>
      {tafsir ? (
        <div className="daily__tafsir">
          <Text size="xs" tone="accent" font="arabic" dir="rtl">
            {tafsir.book_ar}
          </Text>
          <Text as="p" size="sm" tone="muted">
            {tafsir.excerpt_en}
          </Text>
        </div>
      ) : null}
      <ShareButton
        content={{
          kicker: `Qurʾān · ${verse.surah} ${verse.surah_n}:${verse.ayah_n}`,
          arabic: verse.ayah_ar,
          latin: verse.ayah_en,
          source: `Qurʾān ${verse.surah_n}:${verse.ayah_n}`,
          url: window.location.origin,
        }}
        requestShare={requestShare}
      />
    </Card>
  );
}

function HadithCard({ hadith }: { hadith: DailyHadith }) {
  return (
    <Card variant="flat" pad="lg">
      <div className="daily__hadith-head">
        <Text size="xs" tone="faint" weight="semibold" className="daily__label">
          Hadith
        </Text>
        <Badge variant={reliabilityBadge(hadith.grade)}>
          <span dir="rtl">{hadith.grade_label}</span>
        </Badge>
      </div>
      <p className="daily__matn" dir="rtl">
        {hadith.matn_ar}
      </p>
      <p className="daily__matn-en">
        <Text size="md" tone="muted" font="serif">
          {hadith.matn_en}
        </Text>
      </p>
      {hadith.isnad_ar ? (
        <Text as="p" size="sm" tone="faint" font="arabic" dir="rtl">
          {hadith.isnad_ar}
        </Text>
      ) : null}
      <Divider />
      <div className="daily__sources">
        <span className="daily__src">
          <Text size="sm" font="arabic" dir="rtl">
            {hadith.source.book_ar}
          </Text>
          <Text size="xs" tone="faint" font="mono">
            № {hadith.source.n}
          </Text>
          {hadith.source.sect ? <Badge>{hadith.source.sect}</Badge> : null}
        </span>
        {hadith.parallels.map((p) => (
          <span key={`${p.book}-${p.n}`} className="daily__src">
            <Text size="sm" font="arabic" dir="rtl">
              {p.book_ar}
            </Text>
            <Text size="xs" tone="faint" font="mono">
              № {p.n}
            </Text>
          </span>
        ))}
      </div>
    </Card>
  );
}

export interface DailyScreenProps {
  onOpenReader: (urn: string) => void;
}

export function DailyScreen({ onOpenReader }: DailyScreenProps) {
  const { data, error, loading } = useAsync<Daily>(() => getDaily(), []);

  if (loading) return <Spinner label="Loading today’s reading" />;
  if (error || !data) {
    return (
      <Text as="p" size="sm" tone="danger">
        Could not load the daily reading{error ? `: ${error.message}` : ''}.
      </Text>
    );
  }

  return (
    <section>
      <header className="scr__head">
        <Text size="xs" tone="accent" weight="semibold" className="scr__eyebrow">
          Daily · اليوم
        </Text>
        <Heading level={1}>Today’s reading</Heading>
        <Text as="p" size="sm" tone="muted" font="mono">
          {data.date.hijri} · {data.date.gregorian}
        </Text>
      </header>
      <div className="daily__grid">
        <VerseCard verse={data.verse} />
        <HadithCard hadith={data.hadith} />
        <Card variant="raised" pad="lg" className="daily__pick">
          <Text size="xs" tone="accent" weight="semibold" className="daily__label">
            Continue reading
          </Text>
          <Text as="p" size="md" className="daily__rationale">
            {data.book.rationale}
          </Text>
          <Button variant="gold" iconBefore="reader" onClick={() => onOpenReader(data.book.urn)}>
            Open: {data.book.open_to.chapter_en}
          </Button>
        </Card>
      </div>
    </section>
  );
}
