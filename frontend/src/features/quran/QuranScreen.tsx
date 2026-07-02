import { useMemo, useState } from 'react';
import {
  IconButton,
  Input,
  NavArrow,
  Pill,
  Segmented,
  Spinner,
  Text,
  UnstyledButton,
} from '../../lib/design-system';
import { getSurah } from '../../lib/api/client';
import { SURAHS, surahName } from '../../lib/surahs';
import type { SurahName } from '../../lib/surahs';
import type { Ayah, Surah } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { clamp, cx, toArabicDigits } from '../../lib/utils';
import '../../components/HadithBlock.css';
import './QuranScreen.css';

type QuranLang = 'ar' | 'both' | 'en';
type ResearchTab = 'tafsir' | 'lexicon' | 'morphology';

const SURAH_MIN = 1;
const SURAH_MAX = 114;

const LANGS = [
  { value: 'en', label: 'EN' },
  { value: 'both', label: 'EN | AR' },
  { value: 'ar', label: 'AR' },
];

const RESEARCH_TABS = [
  { value: 'tafsir', label: 'Tafsīr' },
  { value: 'lexicon', label: 'Lexicon' },
  { value: 'morphology', label: 'Morphology' },
];

// Placeholder commentary shelf: the panel knows its sources before the tafsīr
// corpus is ingested.
const TAFSIR_SOURCES = [
  { ar: 'الميزان في تفسير القرآن', en: 'al-Mīzān · al-Ṭabāṭabāʾī' },
  { ar: 'مجمع البيان', en: 'Majmaʿ al-Bayān · al-Ṭabrisī' },
  { ar: 'جامع البيان', en: 'Jāmiʿ al-Bayān · al-Ṭabarī' },
];

const BASMALA = 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ';

/** The dedicated Qurʾān reader: a surah rail, verse cards on the reader
    surface, and a bottom research drawer (tafsīr, lexicon, morphology) that
    opens from any verse. */
export function QuranScreen() {
  const [surahN, setSurahN] = useState(SURAH_MIN);
  const [lang, setLang] = useState<QuranLang>('both');
  const [cards, setCards] = useState(true);
  const [filter, setFilter] = useState('');
  const [selected, setSelected] = useState<Ayah | null>(null);
  const [tab, setTab] = useState<ResearchTab>('tafsir');

  const res = useAsync<Surah>(() => getSurah(surahN), [surahN]);
  const name = surahName(surahN);

  const list = useMemo(() => {
    const q = filter.trim();
    if (!q) return SURAHS;
    const lower = q.toLowerCase();
    return SURAHS.filter(
      (s) => s.en.toLowerCase().includes(lower) || s.ar.includes(q) || String(s.n) === q,
    );
  }, [filter]);

  const goSurah = (n: number) => {
    setSurahN(clamp(n, SURAH_MIN, SURAH_MAX));
    setSelected(null);
  };

  return (
    <div className="quran" data-reader-theme="classical" data-lang={lang}>
      <aside className="quran__rail" aria-label="Surahs">
        <Input
          value={filter}
          type="search"
          icon="search"
          surface="reader"
          hideLabel
          label="Find a sūra"
          placeholder="Find a sūra…"
          onInput={setFilter}
        />
        <ul className="quran__list">
          {list.map((s) => (
            <li key={s.n}>
              <UnstyledButton
                className={cx('quran__surah', s.n === surahN && 'quran__surah--current')}
                onClick={() => goSurah(s.n)}
              >
                <span className="quran__surah-n">{s.n}</span>
                <span className="quran__surah-en">{s.en}</span>
                <span className="quran__surah-ar" dir="rtl">
                  {s.ar}
                </span>
              </UnstyledButton>
            </li>
          ))}
        </ul>
      </aside>

      <main className="quran__main">
        <header className="quran__head">
          <div className="quran__nav">
            {surahN > SURAH_MIN ? (
              <NavArrow
                direction="back"
                surface="reader"
                label={`Sūrat ${surahName(surahN - 1).en}`}
                onClick={() => goSurah(surahN - 1)}
              />
            ) : null}
            <div className="quran__title">
              <h2 className="quran__title-ar" dir="rtl">
                سورة {name.ar}
              </h2>
              <p className="quran__title-en">
                Sūrat {name.en} · {surahN}
                {res.data ? ` · ${res.data.verse_count} āyāt` : ''}
              </p>
            </div>
            {surahN < SURAH_MAX ? (
              <NavArrow
                direction="forward"
                surface="reader"
                label={`Sūrat ${surahName(surahN + 1).en}`}
                onClick={() => goSurah(surahN + 1)}
              />
            ) : null}
          </div>
          <div className="quran__controls">
            <Segmented
              surface="reader"
              label="Language"
              value={lang}
              options={LANGS}
              onChange={(v) => setLang(v as QuranLang)}
            />
            <Pill surface="reader" active={cards} icon="grid" onClick={() => setCards((c) => !c)}>
              Cards
            </Pill>
          </div>
        </header>

        <article className="quran__verses" data-cards={cards ? 'on' : 'off'}>
          {surahN !== 1 && surahN !== 9 ? (
            <p className="quran__basmala" dir="rtl">
              {BASMALA}
            </p>
          ) : null}
          {res.loading ? <Spinner label="Loading sūra" /> : null}
          {res.error ? (
            <Text as="p" size="sm" tone="danger">
              Could not load the sūra: {res.error.message}
            </Text>
          ) : null}
          {res.data?.verses.map((v) => (
            <VerseCard
              key={v.ayah}
              v={v}
              lang={lang}
              active={selected?.ayah === v.ayah}
              onSelect={() => setSelected(v)}
            />
          ))}
        </article>
      </main>

      {selected ? (
        <ResearchDrawer
          verse={selected}
          name={name}
          tab={tab}
          onTab={setTab}
          onClose={() => setSelected(null)}
        />
      ) : null}
    </div>
  );
}

interface VerseCardProps {
  v: Ayah;
  lang: QuranLang;
  active: boolean;
  onSelect: () => void;
}

function VerseCard({ v, lang, active, onSelect }: VerseCardProps) {
  return (
    <section className={cx('hadith', active && 'hadith--active')} tabIndex={0} onClick={onSelect}>
      <header className="hadith__head">
        <span className="hadith__id">
          <span className="hadith__num">{toArabicDigits(v.ayah)}</span>
          <span className="hadith__meta">
            Verse {v.surah}:{v.ayah}
          </span>
        </span>
      </header>
      <div className={cx('hadith__body', lang === 'both' && v.text_en && 'hadith__body--grid')}>
        {lang !== 'ar' && v.text_en ? <p className="hadith__matn-en">{v.text_en}</p> : null}
        {lang !== 'en' ? (
          <p className="hadith__matn-ar" dir="rtl">
            {v.text_ar}
          </p>
        ) : null}
      </div>
    </section>
  );
}

interface ResearchDrawerProps {
  verse: Ayah;
  name: SurahName;
  tab: ResearchTab;
  onTab: (t: ResearchTab) => void;
  onClose: () => void;
}

/** Bottom-up research drawer for one verse. Tafsīr, lexicon and morphology are
    structural placeholders until their corpora are ingested; the drawer is the
    contract for where they land. */
function ResearchDrawer({ verse, name, tab, onTab, onClose }: ResearchDrawerProps) {
  const words = verse.text_plain.split(' ').filter(Boolean);
  return (
    <div className="quran-drawer" role="dialog" aria-label={`Research ${verse.surah}:${verse.ayah}`}>
      <header className="quran-drawer__head">
        <div className="quran-drawer__ref">
          <p className="quran-drawer__label">
            Āya {verse.surah}:{verse.ayah} · {name.en}
          </p>
          <p className="quran-drawer__text" dir="rtl">
            {verse.text_ar}
          </p>
        </div>
        <IconButton surface="reader" size="sm" label="Close" icon="close" onClick={onClose} />
      </header>
      <Segmented
        surface="reader"
        label="Research panel"
        value={tab}
        options={RESEARCH_TABS}
        onChange={(v) => onTab(v as ResearchTab)}
      />
      <div className="quran-drawer__body">
        {tab === 'tafsir' ? (
          <div className="quran-drawer__sources">
            {TAFSIR_SOURCES.map((t) => (
              <article key={t.en} className="quran-drawer__source">
                <p className="quran-drawer__source-name">
                  <span dir="rtl">{t.ar}</span>
                  <span className="quran-drawer__source-en">{t.en}</span>
                </p>
                <Text as="p" size="sm" tone="muted">
                  Commentary on this āya lands here when the tafsīr corpus is ingested.
                </Text>
              </article>
            ))}
          </div>
        ) : (
          <ul className="quran-drawer__words" aria-label="Verse words">
            {words.map((w, i) => (
              <li key={i} className="quran-drawer__word">
                <span className="quran-drawer__word-ar" dir="rtl">
                  {w}
                </span>
                <span className="quran-drawer__word-meta">
                  {tab === 'lexicon' ? 'root · lemma · gloss' : 'part of speech · pattern · case'}
                </span>
              </li>
            ))}
          </ul>
        )}
        {tab !== 'tafsir' ? (
          <Text as="p" size="xs" tone="faint" className="quran-drawer__note">
            Word-level {tab === 'lexicon' ? 'lexicon' : 'morphology'} arrives with the analysis
            pipeline; the layout is already in place.
          </Text>
        ) : null}
      </div>
    </div>
  );
}
