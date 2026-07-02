import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

import {
  Badge,
  Highlight,
  IconButton,
  IsnadNode,
  NarratorLink,
  Segmented,
  Spinner,
  Text,
} from '../../lib/design-system';
import {
  getBook,
  getCanonicalEntry,
  getRijalEntry,
  getPage,
  getToc,
  searchBook,
} from '../../lib/api/client';
import { READER } from '../../lib/constants';
import { hadithBadge, reliabilityBadge } from '../../lib/variants';
import { annotateText, buildNarratorIndex, canonicalToRecord, rijalToRecord } from '../../lib/narrators';
import type { NarratorIndex } from '../../lib/narrators';
import type {
  BookPage,
  BookSearchMatch,
  Hadith,
  Narrator,
  NarratorRecord,
  Page,
} from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useDomains } from '../../lib/useDomains';
import { clamp, cx, toArabicDigits } from '../../lib/utils';
import { MatchList, TocDrawer } from './ReaderDrawers';
import { RawPageText } from './RawPageText';
import { ReaderToolbar } from './ReaderToolbar';
import type { LeftDrawer, ReaderLang, ReaderTheme, RightDrawer } from './ReaderToolbar';
import './reader.css';
import '../../components/HadithBlock.css';
import './IsnadSidebar.css';
import './NarratorTarjama.css';

const MIN_QUERY = 2;
const EMPTY_MATCHES: Page<BookSearchMatch> = { items: [], total: 0, limit: 0, offset: 0 };

/** Promote a served narrator to a registry-shaped record. A linked narrator
    carries its registry id (resolved at build time); the click handler then
    fetches the full biography. An unlinked one shows name-only (id -1). */
function recordFromNarrator(n: Narrator): NarratorRecord {
  return {
    id: n.rijal_id ?? n.canonical_id ?? -1,
    full_name: n.name_ar || n.name,
    kunya: '',
    nisba: '',
    tradition: '',
    birth_year: '',
    death_year: n.d ? String(n.d) : '',
    teacher_count: 0,
    student_count: 0,
    reliability_term: n.grade,
    origin: n.canonical_id != null ? 'canonical' : 'rijal',
  };
}

function PageHead({ page }: { page: BookPage }) {
  return (
    <header className="reader-pagehead">
      <p className="reader-eyebrow">
        Page {page.page_number} of {page.total_pages}
      </p>
      {page.chapter_title ? (
        <h2 className="reader-chapter" dir="rtl">
          {page.chapter_title}
        </h2>
      ) : null}
      {page.section_title ? (
        <p className="reader-section-ar" dir="rtl">
          {page.section_title}
        </p>
      ) : null}
      {page.section_title_en ? <p className="reader-section-en">{page.section_title_en}</p> : null}
    </header>
  );
}

interface HadithUnitProps {
  h: Hadith;
  active: boolean;
  lang: ReaderLang;
  index: NarratorIndex;
  activeNarrator: string;
  highlight: string;
  onSelect: () => void;
  onNarrator: (record: NarratorRecord) => void;
}

function HadithUnit({
  h,
  active,
  lang,
  index,
  activeNarrator,
  highlight,
  onSelect,
  onNarrator,
}: HadithUnitProps) {
  const segs = annotateText(h.isnad_ar, index);
  return (
    <section className={cx('hadith', active && 'hadith--active')} tabIndex={0} onClick={onSelect}>
      <header className="hadith__head">
        <span className="hadith__id">
          <span className="hadith__num">{toArabicDigits(h.n)}</span>
          <span className="hadith__meta">
            Hadith {h.n} · {h.narrators.length} narrators
          </span>
        </span>
        {h.grade ? (
          <Badge surface="reader" variant={hadithBadge(h.grade)} dot dir="rtl">
            {h.grade}
          </Badge>
        ) : null}
      </header>
      {lang !== 'en' && h.isnad_ar ? (
        <p className="hadith__isnad" dir="rtl">
          {segs.map((s, i) =>
            s.type === 'narrator' ? (
              <NarratorLink
                key={i}
                active={activeNarrator === s.record.full_name}
                onActivate={() => onNarrator(s.record)}
              >
                {s.value}
              </NarratorLink>
            ) : (
              <span key={i}>{s.value}</span>
            ),
          )}
        </p>
      ) : null}
      <div className={cx('hadith__body', lang === 'both' && 'hadith__body--grid')}>
        {lang !== 'ar' && h.matn_en ? (
          <p className="hadith__matn-en">
            <Highlight text={h.matn_en} query={highlight} />
          </p>
        ) : null}
        {lang !== 'en' ? (
          <p className="hadith__matn-ar" dir="rtl">
            <Highlight text={h.matn_ar} query={highlight} />
          </p>
        ) : null}
      </div>
      {h.cross_refs.length ? (
        <div className="hadith__refs">
          <span className="hadith__refs-label">Parallels</span>
          {h.cross_refs.map((r, i) => (
            <span key={i} className="ref-pill">
              <span className="ref-pill__ar" dir="rtl">
                {r.book_ar}
              </span>
              {r.page ? <span className="ref-pill__pg">{r.page}</span> : null}
            </span>
          ))}
        </div>
      ) : null}
    </section>
  );
}

const ISNAD_VIEWS = [
  { value: 'tree', label: 'Tree' },
  { value: 'flow', label: 'Flow' },
  { value: 'cards', label: 'Cards' },
];
type IsnadView = 'tree' | 'flow' | 'cards';

function IsnadPanel({ hadith, onNarrator }: { hadith: Hadith; onNarrator: (n: Narrator) => void }) {
  const [view, setView] = useState<IsnadView>('tree');
  return (
    <aside className="reader-isnad" aria-label="Isnād, transmission chain">
      <div className="reader-isnad__head">
        <p className="reader-isnad__label">Isnād · transmission chain</p>
        <p className="reader-isnad__sub">
          Hadith {hadith.n} · {hadith.narrators.length} narrators
          {hadith.grade ? ` · ${hadith.grade}` : ''}
        </p>
      </div>
      <div className="reader-isnad__views">
        <Segmented
          surface="reader"
          label="Isnād layout"
          value={view}
          options={ISNAD_VIEWS}
          onChange={(v) => setView(v as IsnadView)}
        />
      </div>
      {hadith.narrators.length === 0 ? (
        <p className="reader-isnad__empty">No transmission chain recorded for this unit.</p>
      ) : (
        <div className={`isnad-chain isnad-chain--${view}`}>
          {hadith.narrators.map((n, i) => (
            <IsnadNode
              key={i}
              variant={view === 'cards' ? 'card' : view === 'flow' ? 'flow' : 'tree'}
              index={i}
              showLine={view === 'tree' && i < hadith.narrators.length - 1}
              nameEn={n.name || n.name_ar}
              nameAr={n.name_ar}
              died={n.d}
              role={n.role}
              grade={n.grade}
              gradeVariant={reliabilityBadge(n.grade)}
              onClick={() => onNarrator(n)}
            />
          ))}
        </div>
      )}
    </aside>
  );
}

function narratorSource(record: NarratorRecord): string {
  if (record.id < 0) return 'Extracted from the text · no registry entry';
  return record.origin === 'canonical' ? 'Canonical narrator registry' : 'Rijāl registry';
}

interface NarratorFetchError {
  id: number;
  origin: NarratorRecord['origin'];
  message: string;
}

function TarjamaPanel({
  record,
  error,
  onClose,
}: {
  record: NarratorRecord;
  error: string | null;
  onClose: () => void;
}) {
  const sub = [record.kunya, record.nisba].filter(Boolean).join(' · ');
  const facts: [string, string | number][] = [
    ['Tradition', record.tradition || '—'],
    ['Died', record.death_year || '—'],
    ['Teachers', record.teacher_count],
    ['Students', record.student_count],
    ...(record.evaluator ? ([['Evaluator', record.evaluator]] as [string, string][]) : []),
    ['Source', record.source_label || '—'],
  ];
  return (
    <aside className="narrator" aria-label="Narrator biography">
      <div className="narrator__head">
        <p className="narrator__label">Tarjama · ترجمة</p>
        <IconButton surface="reader" size="sm" label="Close" icon="close" onClick={onClose} />
      </div>
      <p className="narrator__name" dir="rtl">
        {record.full_name}
      </p>
      {sub ? (
        <p className="narrator__sub" dir="rtl">
          {sub}
        </p>
      ) : null}
      {record.reliability_term ? (
        <div className="narrator__grade">
          <Badge surface="reader" variant={reliabilityBadge(record.reliability_term)} dir="rtl">
            {record.reliability_term}
          </Badge>
        </div>
      ) : null}
      <dl className="narrator__facts">
        {facts.map(([k, v]) => (
          <div key={k} className="narrator__fact">
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
      {error ? (
        <p className="narrator__error" role="alert">
          Biography failed to load · {error}
        </p>
      ) : null}
      <p className="narrator__source">{narratorSource(record)}</p>
    </aside>
  );
}

function Unavailable({ title }: { title: string }) {
  return (
    <div className="reader-unavailable">
      <Text as="p" size="lg" font="serif">
        Not available to read yet
      </Text>
      <Text as="p" size="sm" tone="muted">
        {title} has catalogue metadata, but its page content has not been ingested into the corpus
        yet.
      </Text>
    </div>
  );
}

export interface ReaderScreenProps {
  urn: string;
  page: number;
  initialQuery?: string;
  onPage: (page: number) => void;
  onBack: () => void;
}

export function ReaderScreen({ urn, page, initialQuery = '', onPage, onBack }: ReaderScreenProps) {
  const [readerTheme, setReaderTheme] = useState<ReaderTheme>('classical');
  const [lang, setLang] = useState<ReaderLang>('both');
  const [size, setSize] = useState<number>(READER.SIZE_DEFAULT);
  const [left, setLeft] = useState<LeftDrawer>('contents');
  const [right, setRight] = useState<RightDrawer>(null);
  const [activeHadith, setActiveHadith] = useState(0);
  const [narrator, setNarrator] = useState<NarratorRecord | null>(null);
  const [narratorError, setNarratorError] = useState<NarratorFetchError | null>(null);
  const [searchQ, setSearchQ] = useState(initialQuery);

  // App (and the URL) own the page; reset the in-page highlight when it changes.
  useEffect(() => {
    setActiveHadith(0);
  }, [page]);

  const bookRes = useAsync(() => getBook(urn), [urn]);
  const tocRes = useAsync(() => getToc(urn), [urn]);
  const domainsRes = useDomains();
  const pageRes = useAsync<BookPage>(() => getPage(urn, page), [urn, page]);
  const searchRes = useAsync<Page<BookSearchMatch>>(
    () =>
      searchQ.trim().length >= MIN_QUERY
        ? searchBook(urn, searchQ.trim())
        : Promise.resolve(EMPTY_MATCHES),
    [urn, searchQ],
  );

  const pageRecords = useMemo(
    () => (pageRes.data?.hadiths ?? []).flatMap((h) => h.narrators).map(recordFromNarrator),
    [pageRes.data],
  );
  const index = useMemo(() => buildNarratorIndex(pageRecords), [pageRecords]);
  // Category slugs -> human labels, from the taxonomy; the masthead badge shows
  // the label ("Arabic Language Sciences"), never the raw slug.
  const categoryLabels = useMemo(() => {
    const labels = new Map<string, string>();
    for (const domain of domainsRes.data ?? []) {
      for (const category of domain.categories) labels.set(category.slug, category.label);
    }
    return labels;
  }, [domainsRes.data]);

  const openRecord = (record: NarratorRecord) => {
    setNarrator(record);
    setNarratorError(null);
    setRight('tarjama');
    if (record.id < 0) return;
    const detail =
      record.origin === 'canonical'
        ? getCanonicalEntry(record.id).then(canonicalToRecord)
        : getRijalEntry(record.id).then(rijalToRecord);
    detail
      .then((full) =>
        setNarrator((current) =>
          current && current.id === record.id && current.origin === record.origin ? full : current,
        ),
      )
      .catch((err: unknown) =>
        setNarratorError({
          id: record.id,
          origin: record.origin,
          message: err instanceof Error ? err.message : String(err),
        }),
      );
  };
  const openNarrator = (n: Narrator) => openRecord(recordFromNarrator(n));
  const rootStyle = { '--reader-size': `${size}px` } as CSSProperties;

  const book = bookRes.data;
  const categoryLabel = book ? categoryLabels.get(book.category) : undefined;
  const volume = book?.volume ?? null;
  const death = book?.death_year_ah ? `d. ${book.death_year_ah} AH` : null;
  const toc = tocRes.data;
  const pageData = pageRes.data;
  const hadiths = pageData?.hadiths ?? [];
  const active = hadiths[activeHadith];
  const title = book?.title_ar ?? urn;
  const totalPages = pageData?.total_pages ?? book?.page_count ?? 1;
  // The toolbar's in-book field drives searchQ; a live query shows results in the
  // left drawer and highlights the page. Both read from this one flag.
  const searchActive = searchQ.trim().length >= MIN_QUERY;
  const highlight = searchActive ? searchQ.trim() : '';

  return (
    <div className="reader-root" data-reader-theme={readerTheme} data-lang={lang} style={rootStyle}>
      <ReaderToolbar
        titleAr={book?.title_ar ?? '…'}
        titleEn={book?.title_en}
        author={book?.author ?? book?.author_ar}
        categoryLabel={categoryLabel}
        volume={volume}
        death={death}
        page={page}
        totalPages={totalPages}
        readerTheme={readerTheme}
        lang={lang}
        size={size}
        leftDrawer={left}
        rightDrawer={right}
        searchQuery={searchQ}
        onSearchQuery={setSearchQ}
        onClearSearch={() => setSearchQ('')}
        onBack={onBack}
        onPage={onPage}
        onTheme={setReaderTheme}
        onLang={setLang}
        onSize={(s) => setSize(clamp(s, READER.SIZE_MIN, READER.SIZE_MAX))}
        onLeft={setLeft}
        onRight={(d) => {
          setRight(d);
          if (d !== 'tarjama') setNarrator(null);
        }}
      />
      <div className="reader-body">
        {searchActive ? (
          <MatchList
            query={searchQ.trim()}
            results={searchRes.data?.items ?? []}
            total={searchRes.data?.total ?? 0}
            loading={searchRes.loading}
            onJump={onPage}
          />
        ) : left === 'contents' && toc ? (
          <TocDrawer toc={toc} current={page} onJump={onPage} />
        ) : null}
        <main className="reader-main">
          {pageRes.loading ? <Spinner label="Loading page" /> : null}
          {pageRes.error ? <Unavailable title={title} /> : null}
          {pageData ? (
            <article className="reader-article">
              <PageHead page={pageData} />
              <div>
                {hadiths.length > 0 ? (
                  hadiths.map((h, i) => (
                    <HadithUnit
                      key={h.n}
                      h={h}
                      active={i === activeHadith}
                      lang={lang}
                      index={index}
                      activeNarrator={narrator?.full_name ?? ''}
                      highlight={highlight}
                      onSelect={() => setActiveHadith(i)}
                      onNarrator={openRecord}
                    />
                  ))
                ) : pageData.text_ar ? (
                  <RawPageText
                    textAr={pageData.text_ar}
                    textEn={pageData.text_en}
                    lang={lang}
                    highlight={highlight}
                  />
                ) : null}
              </div>
            </article>
          ) : null}
        </main>
        {right === 'isnad' && active ? (
          <IsnadPanel hadith={active} onNarrator={openNarrator} />
        ) : null}
        {right === 'tarjama' && narrator ? (
          <TarjamaPanel
            record={narrator}
            error={
              narratorError &&
              narratorError.id === narrator.id &&
              narratorError.origin === narrator.origin
                ? narratorError.message
                : null
            }
            onClose={() => {
              setRight(null);
              setNarrator(null);
              setNarratorError(null);
            }}
          />
        ) : null}
      </div>
    </div>
  );
}
