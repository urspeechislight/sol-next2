import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { Eyebrow, ShareButton, Text, UnstyledButton } from '../../lib/design-system';
import { HOME } from '../../lib/constants';
import { requestShare } from '../../lib/share';
import { surahName } from '../../lib/surahs';
import type { Tafsir, Verse } from '../../lib/types';
import './VerseOfDay.css';

export interface VerseOfDayProps {
  verse: Verse;
  onOpenReader: (urn: string, page?: number) => void;
}

/** The folio's matn: today's ayah at display scale, unfurling word by word
    (click to replay), the translation beneath it, and the two tafsīr excerpts
    set as a footnote apparatus — the cross-tradition pairing side by side,
    each linked into its commentary at the cited page. Open composition, no
    card chrome: the verse is the page, not a widget on it. */
export function VerseOfDay({ verse, onOpenReader }: VerseOfDayProps) {
  const surah = surahName(verse.surah_n);
  return (
    <article className="vhero" aria-label="Verse of the day">
      <header className="vhero__head">
        <Eyebrow>Verse of the day · آية اليوم</Eyebrow>
        <Text size="xs" tone="faint" font="mono">
          Qurʾān {verse.surah_n}:{verse.ayah_n}
        </Text>
      </header>

      <AyahCartouche ayahAr={verse.ayah_ar} />

      <p className="vhero__surah" dir="rtl">
        {surah.ar}
        <span className="vhero__surah-en" dir="ltr">
          Sūrat {surah.en}
        </span>
      </p>

      {verse.ayah_en ? <p className="vhero__en">{verse.ayah_en}</p> : null}

      <TafsirApparatus tafsirs={verse.tafsirs} onOpenReader={onOpenReader} />

      <footer className="vhero__foot">
        <ShareButton
          content={{
            kicker: `Qurʾān · ${surah.en} ${verse.surah_n}:${verse.ayah_n}`,
            arabic: verse.ayah_ar,
            latin: verse.ayah_en ?? '',
            source: `Qurʾān ${verse.surah_n}:${verse.ayah_n}`,
            url: window.location.origin,
          }}
          requestShare={requestShare}
        />
      </footer>
    </article>
  );
}

/** The ayah itself: hero-scale Arabic that reveals one word per tick, resting
    between loops. Clicking replays the recitation from the first word. */
function AyahCartouche({ ayahAr }: { ayahAr: string }) {
  const words = useMemo(() => ayahAr.split(' ').filter(Boolean), [ayahAr]);
  const cycle = words.length + HOME.VERSE_HOLD_TICKS;

  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => (t + 1) % cycle), HOME.VERSE_WORD_MS);
    return () => clearInterval(id);
  }, [cycle]);
  const shown = Math.min(tick + 1, words.length);
  const progressStyle = { '--vday-progress': shown / words.length } as CSSProperties;

  return (
    <UnstyledButton
      className="vhero__cartouche"
      onClick={() => setTick(0)}
      title="Replay the recitation"
    >
      <span className="vhero__words" dir="rtl">
        {words.map((w, i) => (
          <span
            key={i}
            className={
              i < shown
                ? i === shown - 1
                  ? 'vhero__word vhero__word--in vhero__word--cursor'
                  : 'vhero__word vhero__word--in'
                : 'vhero__word'
            }
          >
            {w}
            {i < words.length - 1 ? ' ' : ''}
          </span>
        ))}
      </span>
      <span className="vhero__progress" style={progressStyle} aria-hidden="true" />
    </UnstyledButton>
  );
}

interface TafsirApparatusProps {
  tafsirs: Tafsir[];
  onOpenReader: (urn: string, page?: number) => void;
}

/** The footnote apparatus: every excerpt visible at once, side by side, the
    way a manuscript sets commentary under the matn. A cited work the corpus
    holds links into the reader at its page; one it does not hold is quoted
    and left unlinked. */
function TafsirApparatus({ tafsirs, onOpenReader }: TafsirApparatusProps) {
  return (
    <div className="vhero__tafsir">
      <div className="vhero__tafsir-rule" aria-hidden="true">
        <span className="vhero__tafsir-label">Tafsīr · التفسير</span>
      </div>
      <div className="vhero__tafsir-cols">
        {tafsirs.map((t) => (
          <UnstyledButton
            key={t.book}
            className="vhero__excerpt"
            onClick={() => (t.urn ? onOpenReader(t.urn, t.page ?? undefined) : undefined)}
            disabled={!t.urn}
            title={t.urn ? 'Read the commentary in the reader' : 'Not yet in the corpus'}
          >
            <span className="vhero__excerpt-meta">
              <span className="vhero__excerpt-book" dir="rtl">
                {t.book_ar}
              </span>
              <span className="vhero__excerpt-author">{t.author}</span>
            </span>
            <span className="vhero__excerpt-text">{t.excerpt_en}</span>
            {t.urn ? <span className="vhero__excerpt-go">Read the commentary →</span> : null}
          </UnstyledButton>
        ))}
      </div>
    </div>
  );
}
