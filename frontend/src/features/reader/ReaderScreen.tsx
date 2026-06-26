import { useMemo, useState } from "react";
import type { CSSProperties } from "react";
import { Icon } from "../../lib/design-system";
import type { IconName } from "../../lib/design-system";
import { annotateText, buildNarratorIndex, type NarratorIndex } from "../../lib/narrators";
import { READER } from "../../lib/constants";
import { ReaderToolbar } from "./ReaderToolbar";
import type { LeftDrawer, ReaderLang, ReaderTheme, RightDrawer } from "./ReaderToolbar";
import {
  CHAIN_ORDER, HADITHS, MATCHES, NARRATORS, TOC,
  engGrade, isnadTone, narratorRecords, relTone, type ReaderHadith,
} from "./readerData";
import "./reader.css";
import "../../components/HadithBlock.css";
import "./IsnadSidebar.css";
import "./NarratorTarjama.css";

type IsnadStyle = "tree" | "horizontal" | "cards";

function PageHead() {
  return (
    <header className="reader-pagehead">
      <p className="reader-eyebrow">Page 109 · The contingency of the world and the affirmation of its Originator</p>
      <h2 className="reader-chapter" dir="rtl">كِتَابُ التَّوْحِيد</h2>
      <p className="reader-section-ar" dir="rtl">بَابُ حُدُوثِ الْعَالَمِ وَإِثْبَاتِ الْمُحْدِث</p>
      <p className="reader-section-en">The Book of Divine Unity · Chapter: the contingency of the world and the affirmation of its Originator</p>
    </header>
  );
}

function TocDrawer() {
  return (
    <aside className="reader-toc" aria-label="Table of contents">
      <p className="reader-toc__label">Contents</p>
      {TOC.map((t) => (
        <button key={t.pg} className="reader-toc__item" aria-current={t.current || undefined}>
          <span>
            <span className="reader-toc__ar" dir="rtl">{t.ar}</span>
            <span className="reader-toc__en">{t.en}</span>
          </span>
          <span className="reader-toc__pg">{t.pg}</span>
        </button>
      ))}
    </aside>
  );
}

function SearchDrawer({ query, onQuery }: { query: string; onQuery: (q: string) => void }) {
  const list = MATCHES.filter((m) => !query || m.ar.includes(query) || m.en.toLowerCase().includes(query.toLowerCase()));
  return (
    <aside className="reader-toc" aria-label="Search in book">
      <p className="reader-toc__label">Search in book</p>
      <div className="reader-search__field">
        <Icon name="search" size="sm" />
        <input value={query} placeholder="ابحث في الكتاب…" dir="rtl" aria-label="Search" onChange={(e) => onQuery(e.target.value)} />
      </div>
      <p className="reader-search__hint">Arabic queries are normalized (diacritics, definite article).</p>
      {list.length ? list.map((m, i) => (
        <button key={i} className="reader-match">
          <div className="reader-match__pg">page {m.pg}</div>
          <div className="reader-match__ar" dir="rtl">{m.ar}</div>
          <div className="reader-match__en">{m.en}</div>
        </button>
      )) : <p className="reader-search__hint">No matches.</p>}
    </aside>
  );
}

interface HadithUnitProps {
  h: ReaderHadith;
  active: boolean;
  lang: ReaderLang;
  index: NarratorIndex;
  activeNarrator: string | null;
  onSelect: () => void;
  onNarrator: (id: string) => void;
}

function HadithUnit({ h, active, lang, index, activeNarrator, onSelect, onNarrator }: HadithUnitProps) {
  const segs = annotateText(h.isnadAr, index);
  return (
    <section className={`hadith${active ? " hadith--active" : ""}`} tabIndex={0} onClick={onSelect}>
      <header className="hadith__head">
        <span className="hadith__id">
          <span className="hadith__num">{h.num}</span>
          <span className="hadith__meta">{h.narrators} narrators</span>
        </span>
        <span className="hadith__grade" dir="rtl"><i /> {h.grade}</span>
      </header>
      {lang !== "en" ? (
        <p className="hadith__isnad" dir="rtl">
          {segs.map((s, i) => s.type === "narrator"
            ? (
              <button key={i} type="button" className="narrator-link" data-on={activeNarrator === s.record.id ? "" : undefined}
                onClick={(e) => { e.stopPropagation(); onNarrator(s.record.id); }}>{s.value}</button>
            )
            : <span key={i}>{s.value}</span>)}
        </p>
      ) : null}
      {lang === "en" ? <p className="hadith__isnad-en">{h.isnadEn}</p> : null}
      <div className={`hadith__body${lang === "both" ? " hadith__body--grid" : ""}`}>
        {lang !== "ar" ? <p className="hadith__matn-en">{h.matnEn}</p> : null}
        {lang !== "en" ? <p className="hadith__matn-ar" dir="rtl">{h.matnAr}</p> : null}
      </div>
      <div className="hadith__refs">
        <span className="hadith__refs-label">Parallels</span>
        {h.refs.map((r, i) => (
          <span key={i} className="ref-pill">
            <span className="ref-pill__ar" dir="rtl">{r.ar}</span>
            <span className="ref-pill__pg">{r.pg}</span>
          </span>
        ))}
      </div>
    </section>
  );
}

const ISNAD_STYLES: [IsnadStyle, string, IconName][] = [
  ["tree", "Tree", "layers"], ["horizontal", "Flow", "menu"], ["cards", "Cards", "grid"],
];

function IsnadPanel({ activeHadith, style, onStyle }: { activeHadith: number; style: IsnadStyle; onStyle: (s: IsnadStyle) => void }) {
  return (
    <aside className="reader-isnad" aria-label="Isnād, transmission chain">
      <div className="reader-isnad__head">
        <p className="reader-isnad__label">Isnād · transmission chain</p>
        <p className="reader-isnad__sub">Hadith {activeHadith + 1} · {CHAIN_ORDER.length} narrators · {HADITHS[activeHadith].grade}</p>
      </div>
      <div className="isnad-styles">
        <div className="reader-seg" role="radiogroup" aria-label="Chain view">
          {ISNAD_STYLES.map(([v, label, icon]) => (
            <button key={v} className="reader-seg__btn" aria-pressed={v === style} onClick={() => onStyle(v)}><Icon name={icon} size="sm" />{label}</button>
          ))}
        </div>
      </div>
      <div className={`isnad-chain isnad-chain--${style}`}>
        {CHAIN_ORDER.map((id, i) => {
          const r = NARRATORS.find((n) => n.id === id);
          if (!r) return null;
          const tone = isnadTone(r.grade);
          return (
            <div key={id} className="isnad-node">
              {i < CHAIN_ORDER.length - 1 ? <span className="isnad-node__line" /> : null}
              <span className={`isnad-node__dot${i === 0 ? " isnad-node__dot--origin" : ""}`}>{i === 0 ? "★" : i}</span>
              <div className="isnad-node__body">
                <p className="isnad-node__en">{r.en || r.fullName}</p>
                <p className="isnad-node__meta">d. {r.deathYear || "—"} · {r.role}</p>
                <span className={`isnad-node__grade${tone ? ` isnad-node__grade--${tone}` : ""}`}>{engGrade(r.grade)}</span>
              </div>
              <p className="isnad-node__ar" dir="rtl">{r.fullName}</p>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function TarjamaPanel({ id, onClose }: { id: string; onClose: () => void }) {
  const r = NARRATORS.find((n) => n.id === id);
  if (!r) return null;
  const sub = [r.kunya, r.nisba].filter(Boolean).join(" · ");
  const facts: [string, string | number][] = [
    ["Tradition", r.tradition], ["Died", r.deathYear || "—"], ["Teachers", r.teacherCount], ["Students", r.studentCount],
    ...(r.evaluator ? ([["Evaluator", r.evaluator]] as [string, string][]) : []), ["Role", r.role],
  ];
  return (
    <aside className="narrator" aria-label="Narrator biography">
      <div className="narrator__head">
        <p className="narrator__label">Tarjama · ترجمة</p>
        <button className="reader-iconbtn reader-iconbtn--sm" aria-label="Close" onClick={onClose}><Icon name="close" size="sm" /></button>
      </div>
      <p className="narrator__name" dir="rtl">{r.fullName}</p>
      <p className="narrator__sub" dir="rtl">{sub}</p>
      <span className={`narrator-grade narrator-grade--${relTone(r.grade)}`} dir="rtl">{r.term}</span>
      <dl className="narrator__facts">
        {facts.map(([k, v]) => <div key={k} className="narrator__fact"><dt>{k}</dt><dd>{v}</dd></div>)}
      </dl>
      <p className="narrator__source">Rijāl registry · linked by name</p>
    </aside>
  );
}

export interface ReaderScreenProps {
  onBack: () => void;
}

export function ReaderScreen({ onBack }: ReaderScreenProps) {
  const [page, setPage] = useState(109);
  const [readerTheme, setReaderTheme] = useState<ReaderTheme>("classical");
  const [lang, setLang] = useState<ReaderLang>("both");
  const [size, setSize] = useState<number>(READER.SIZE_DEFAULT);
  const [left, setLeft] = useState<LeftDrawer>("contents");
  const [right, setRight] = useState<RightDrawer>(null);
  const [activeHadith, setActiveHadith] = useState(0);
  const [narratorId, setNarratorId] = useState<string | null>(null);
  const [isnadStyle, setIsnadStyle] = useState<IsnadStyle>("tree");
  const [query, setQuery] = useState("");

  const index = useMemo(() => buildNarratorIndex(narratorRecords()), []);
  const totalPages = 14200;
  const rootStyle = { "--reader-size": `${size}px` } as CSSProperties;
  const clamp = (n: number) => Math.max(READER.SIZE_MIN, Math.min(READER.SIZE_MAX, n));
  const openNarrator = (id: string) => { setNarratorId(id); setRight("tarjama"); };

  return (
    <div className="reader-root" data-reader-theme={readerTheme} data-lang={lang} style={rootStyle}>
      <ReaderToolbar
        page={page} totalPages={totalPages} readerTheme={readerTheme} lang={lang} size={size}
        leftDrawer={left} rightDrawer={right}
        onBack={onBack} onPage={setPage} onTheme={setReaderTheme} onLang={setLang}
        onSize={(s) => setSize(clamp(s))}
        onLeft={setLeft}
        onRight={(d) => { setRight(d); if (d !== "tarjama") setNarratorId(null); }}
      />
      <div className="reader-body">
        {left === "contents" ? <TocDrawer /> : null}
        {left === "search" ? <SearchDrawer query={query} onQuery={setQuery} /> : null}
        <main className="reader-main">
          <article className="reader-article">
            <PageHead />
            <div>
              {HADITHS.map((h, i) => (
                <HadithUnit
                  key={i} h={h} active={i === activeHadith} lang={lang} index={index}
                  activeNarrator={narratorId} onSelect={() => setActiveHadith(i)} onNarrator={openNarrator}
                />
              ))}
            </div>
          </article>
        </main>
        {right === "isnad" ? <IsnadPanel activeHadith={activeHadith} style={isnadStyle} onStyle={setIsnadStyle} /> : null}
        {right === "tarjama" && narratorId ? <TarjamaPanel id={narratorId} onClose={() => { setRight(null); setNarratorId(null); }} /> : null}
      </div>
      <div className="reader-progress">
        <div className="reader-progress__fill" style={{ width: `${((page / totalPages) * 100).toFixed(1)}%` }} />
      </div>
    </div>
  );
}
