import type { CSSProperties } from 'react';
import { useEffect, useMemo, useState } from 'react';
import { ShareButton, Text, UnstyledButton } from '../../lib/design-system';
import { HOME } from '../../lib/constants';
import { requestShare } from '../../lib/share';
import type { Verse } from '../../lib/types';
import './VerseOfDay.css';

export interface VerseOfDayProps {
  verse: Verse;
  onOpenReader: (urn: string) => void;
}

/** The landing verse: the ayah unfurls word by word on a slow loop (click the
    cartouche to replay), the translation sits beneath it, and the tafsīr
    excerpts rotate — each one a doorway into its commentary in the reader. */
export function VerseOfDay({ verse, onOpenReader }: VerseOfDayProps) {
  const words = useMemo(() => verse.ayah_ar.split(' ').filter(Boolean), [verse.ayah_ar]);
  const cycle = words.length + HOME.VERSE_HOLD_TICKS;

  const [tick, setTick] = useState(0);
  useEffect(() => {
    const id = setInterval(() => setTick((t) => (t + 1) % cycle), HOME.VERSE_WORD_MS);
    return () => clearInterval(id);
  }, [cycle]);
  const shown = Math.min(tick + 1, words.length);

  const [tafsirIdx, setTafsirIdx] = useState(0);
  useEffect(() => {
    if (verse.tafsirs.length < 2) return;
    const id = setInterval(
      () => setTafsirIdx((i) => (i + 1) % verse.tafsirs.length),
      HOME.TAFSIR_ROTATE_MS,
    );
    return () => clearInterval(id);
  }, [verse.tafsirs.length]);

  const progressStyle = { '--vday-progress': shown / words.length } as CSSProperties;

  return (
    <section className="vday" aria-labelledby="vday-surah">
      <header className="vday__head">
        <Text size="xs" tone="accent" weight="semibold" className="vday__eyebrow">
          Verse of the day · آية اليوم
        </Text>
        <Text size="xs" tone="faint" font="mono">
          Qurʾān {verse.surah_n}:{verse.ayah_n}
        </Text>
      </header>

      <h2 id="vday-surah" className="vday__surah" dir="rtl">
        {verse.surah_ar}
        <span className="vday__surah-en" dir="ltr">
          Sūrat {verse.surah}
        </span>
      </h2>

      <UnstyledButton
        className="vday__cartouche"
        onClick={() => setTick(0)}
        title="Replay the recitation"
      >
        <span className="vday__words" dir="rtl">
          {words.map((w, i) => (
            <span
              key={i}
              className={
                i < shown
                  ? i === shown - 1
                    ? 'vday__word vday__word--in vday__word--cursor'
                    : 'vday__word vday__word--in'
                  : 'vday__word'
              }
            >
              {w}
              {i < words.length - 1 ? ' ' : ''}
            </span>
          ))}
        </span>
        <span className="vday__progress" style={progressStyle} aria-hidden="true" />
      </UnstyledButton>

      <p className="vday__en">{verse.ayah_en}</p>

      <div className="vday__tafsir">
        <div className="vday__tafsir-head">
          <span className="vday__tafsir-label">Tafsīr</span>
          {verse.tafsirs.length > 1 ? (
            <div className="vday__dots" aria-label="Tafsīr excerpts">
              {verse.tafsirs.map((t, i) => (
                <UnstyledButton
                  key={t.book}
                  className={i === tafsirIdx ? 'vday__dot vday__dot--active' : 'vday__dot'}
                  onClick={() => setTafsirIdx(i)}
                  ariaLabel={`Show tafsīr from ${t.book}`}
                />
              ))}
            </div>
          ) : null}
        </div>
        <div className="vday__tafsir-stage">
          {verse.tafsirs.map((t, i) => (
            <UnstyledButton
              key={t.book}
              className={
                i === tafsirIdx ? 'vday__tafsir-card vday__tafsir-card--active' : 'vday__tafsir-card'
              }
              onClick={() => (t.urn ? onOpenReader(t.urn) : undefined)}
              disabled={!t.urn}
              tabIndex={i === tafsirIdx ? 0 : -1}
            >
              <span className="vday__tafsir-meta">
                <span className="vday__tafsir-book" dir="rtl">
                  {t.book_ar}
                </span>
                <span className="vday__tafsir-author">{t.author}</span>
              </span>
              <span className="vday__tafsir-text">{t.excerpt_en}</span>
              {t.urn ? <span className="vday__tafsir-go">Read the commentary →</span> : null}
            </UnstyledButton>
          ))}
        </div>
      </div>

      <footer className="vday__foot">
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
      </footer>
    </section>
  );
}
