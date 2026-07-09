import { useEffect, useState } from 'react';
import {
  Card,
  Highlight,
  IconButton,
  NavArrow,
  PageGlow,
  Pill,
  Segmented,
  Spinner,
  Text,
} from '../../lib/design-system';
import type { LockupMode } from '../../lib/design-system';
import { getSurah } from '../../lib/api/client';
import { LANG_OPTIONS } from '../../lib/constants';
import { SURAH_COUNT, surahName, verseMatches } from '../../lib/surahs';
import type { SurahName, VerseRef } from '../../lib/surahs';
import type { Ayah, Surah } from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useTheme } from '../../lib/useTheme';
import { clamp, cx, toArabicDigits } from '../../lib/utils';
import { countLabel } from '../../lib/utils';
import { SuraFinder } from './SuraFinder';
import '../../components/HadithBlock.css';
import './QuranScreen.css';

type QuranLang = LockupMode;
type ResearchTab = 'tafsir' | 'lexicon' | 'morphology';

const SURAH_MIN = 1;
const SURAH_MAX = SURAH_COUNT;

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

export interface QuranScreenProps {
  /** The header's sūra-scoped search term (submitted, not live): filters the
      open sūra's āyāt in place; '' shows the whole sūra. */
  query?: string;
  /** A verse to open focused, e.g. from a citation link in the reader. */
  focus?: VerseRef | null;
}

/** The dedicated Qurʾān reader: a surah rail with the shared Qurʾān finder,
    verse cards on the reader surface (filterable in place by the header's
    sūra-scoped search), and a bottom research drawer (tafsīr, lexicon,
    morphology) that opens from any verse. */
export function QuranScreen({ query = '', focus = null }: QuranScreenProps) {
  const { dark } = useTheme();
  const [surahN, setSurahN] = useState(SURAH_MIN);
  const [lang, setLang] = useState<QuranLang>('both');
  const [cards, setCards] = useState(true);
  const [selected, setSelected] = useState<Ayah | null>(null);
  const [focusAyah, setFocusAyah] = useState<number | null>(null);
  const [tab, setTab] = useState<ResearchTab>('tafsir');

  const res = useAsync<Surah>(() => getSurah(surahN), [surahN]);
  const name = surahName(surahN);

  const goSurah = (n: number, focusAya: number | null = null) => {
    setSurahN(clamp(n, SURAH_MIN, SURAH_MAX));
    setSelected(null);
    setFocusAyah(focusAya);
  };

  // A citation link (or any external focus) opens that sūra with the āya set as
  // the scroll target; keyed on the primitives so it fires once per verse.
  const focusSurah = focus?.surah ?? null;
  const focusAya = focus?.ayah ?? null;
  useEffect(() => {
    if (focusSurah === null || focusAya === null) return;
    setSurahN(clamp(focusSurah, SURAH_MIN, SURAH_MAX));
    setSelected(null);
    setFocusAyah(focusAya);
  }, [focusSurah, focusAya]);

  const q = query.trim();
  const verses = res.data?.verses ?? [];
  const shown = q ? verses.filter((v) => verseMatches(v, q)) : verses;

  // A finder jump scrolls its verse into view once the sūra has loaded.
  useEffect(() => {
    if (focusAyah === null || !res.data) return;
    document
      .getElementById(`aya-${focusAyah}`)
      ?.scrollIntoView({ block: 'center', behavior: 'smooth' });
  }, [focusAyah, res.data]);

  return (
    <div className="quran" data-reader-theme={dark ? 'dark' : 'classical'} data-lang={lang}>
      <PageGlow />
      <aside className="quran__rail" aria-label="Surahs">
        <SuraFinder currentSurah={surahN} onPick={goSurah} onJump={goSurah} />
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
              options={LANG_OPTIONS}
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
          {q && res.data ? (
            <Text as="p" size="sm" tone="muted" className="quran__matchline">
              {countLabel(shown.length, 'āya', 'āyāt')} of {verses.length} match “{q}”
            </Text>
          ) : null}
          {q && res.data && shown.length === 0 ? (
            <Text as="p" size="sm" tone="muted">
              Nothing in this sūra contains “{q}”. The finder on the left searches the whole Qurʾān.
            </Text>
          ) : null}
          {shown.map((v) => (
            <VerseCard
              key={v.ayah}
              v={v}
              lang={lang}
              query={q}
              active={selected?.ayah === v.ayah || focusAyah === v.ayah}
              onSelect={() => {
                setSelected(v);
                setFocusAyah(null);
              }}
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
  /** The active sūra-scoped search term; matches highlight in both scripts. */
  query?: string;
  active: boolean;
  onSelect: () => void;
}

function VerseCard({ v, lang, query = '', active, onSelect }: VerseCardProps) {
  return (
    <section
      id={`aya-${v.ayah}`}
      className={cx('hadith', active && 'hadith--active')}
      tabIndex={0}
      onClick={onSelect}
    >
      <header className="hadith__head">
        <span className="hadith__id">
          <span className="hadith__num">{toArabicDigits(v.ayah)}</span>
          <span className="hadith__meta">
            Verse {v.surah}:{v.ayah}
          </span>
        </span>
      </header>
      <div className={cx('hadith__body', lang === 'both' && v.text_en && 'hadith__body--grid')}>
        {lang !== 'ar' && v.text_en ? (
          <p className="hadith__matn-en">
            <Highlight text={v.text_en} query={query} />
          </p>
        ) : null}
        {lang !== 'en' ? (
          <p className="hadith__matn-ar" dir="rtl">
            <Highlight text={v.text_ar} query={query} />
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
    <div
      className="quran-drawer"
      role="dialog"
      aria-label={`Research ${verse.surah}:${verse.ayah}`}
    >
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
              <Card key={t.en} as="article" surface="reader" pad="sm">
                <p className="quran-drawer__source-name">
                  <span dir="rtl">{t.ar}</span>
                  <span className="quran-drawer__source-en">{t.en}</span>
                </p>
                <Text as="p" size="sm" tone="muted">
                  Commentary on this āya lands here when the tafsīr corpus is ingested.
                </Text>
              </Card>
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
