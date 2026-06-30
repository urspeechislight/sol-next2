import { useEffect, useMemo, useState } from 'react';
import type { CSSProperties } from 'react';

import {
  Badge,
  Highlight,
  IconButton,
  IsnadNode,
  NarratorLink,
  Spinner,
  Text,
} from '../../lib/design-system';
import { getBook, getNarratorIndex, getPage, getToc, searchBook } from '../../lib/api/client';
import { READER } from '../../lib/constants';
import { hadithBadge, reliabilityBadge } from '../../lib/variants';
import { normalizeName } from '../../lib/arabic';
import { annotateText, buildNarratorIndex } from '../../lib/narrators';
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
import { clamp, cx, toArabicDigits } from '../../lib/utils';
import { MatchList, TocDrawer } from './ReaderDrawers';
import { ReaderToolbar } from './ReaderToolbar';
import type { LeftDrawer, ReaderLang, ReaderTheme, RightDrawer } from './ReaderToolbar';
import './reader.css';
import '../../components/HadithBlock.css';
import './IsnadSidebar.css';
import './NarratorTarjama.css';

const MIN_QUERY = 2;
const EMPTY_MATCHES: Page<BookSearchMatch> = { items: [], total: 0, limit: 0, offset: 0 };

/** Promote a per-hadith narrator to a registry-shaped record (used when the
    name is not present in the rijāl index). */
function recordFromNarrator(n: Narrator): NarratorRecord {
  return {
    id: -1,
    full_name: n.name_ar || n.name,
    kunya: '',
    nisba: '',
    tradition: '',
    birth_year: '',
    death_year: n.d ? String(n.d) : '',
    teacher_count: 0,
    student_count: 0,
    reliability_term: n.grade,
    origin: 'rijal',
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

function IsnadPanel({ hadith, onNarrator }: { hadith: Hadith; onNarrator: (n: Narrator) => void }) {
  return (
    <aside className="reader-isnad" aria-label="Isnād, transmission chain">
      <div className="reader-isnad__head">
        <p className="reader-isnad__label">Isnād · transmission chain</p>
        <p className="reader-isnad__sub">
          {hadith.narrators.length} narrators{hadith.grade ? ` · ${hadith.grade}` : ''}
        </p>
      </div>
      {hadith.narrators.length === 0 ? (
        <p className="reader-isnad__empty">No transmission chain recorded for this unit.</p>
      ) : (
        <div className="isnad-chain">
          {hadith.narrators.map((n, i) => (
            <IsnadNode
              key={i}
              index={i}
              showLine={i < hadith.narrators.length - 1}
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

function TarjamaPanel({ record, onClose }: { record: NarratorRecord; onClose: () => void }) {
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
      <p className="narrator__source">Rijāl registry · linked by name</p>
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
  const [searchQ, setSearchQ] = useState(initialQuery);

  // App (and the URL) own the page; reset the in-page highlight when it changes.
  useEffect(() => {
    setActiveHadith(0);
  }, [page]);

  const bookRes = useAsync(() => getBook(urn), [urn]);
  const tocRes = useAsync(() => getToc(urn), [urn]);
  const indexRes = useAsync(() => getNarratorIndex(), []);
  const pageRes = useAsync<BookPage>(() => getPage(urn, page), [urn, page]);
  const searchRes = useAsync<Page<BookSearchMatch>>(
    () =>
      searchQ.trim().length >= MIN_QUERY
        ? searchBook(urn, searchQ.trim())
        : Promise.resolve(EMPTY_MATCHES),
    [urn, searchQ],
  );

  const records = indexRes.data ?? [];
  const index = useMemo(() => buildNarratorIndex(records), [records]);
  const nameMap = useMemo(
    () => new Map(records.map((r) => [normalizeName(r.full_name), r])),
    [records],
  );

  const openRecord = (record: NarratorRecord) => {
    setNarrator(record);
    setRight('tarjama');
  };
  const openNarrator = (n: Narrator) =>
    openRecord(nameMap.get(normalizeName(n.name_ar)) ?? recordFromNarrator(n));
  const rootStyle = { '--reader-size': `${size}px` } as CSSProperties;

  const book = bookRes.data;
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
        urn={urn}
        page={page}
        totalPages={totalPages}
        readerTheme={readerTheme}
        lang={lang}
        size={size}
        leftDrawer={left}
        rightDrawer={right}
        searchQuery={searchQ}
        onSearchQuery={setSearchQ}
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
          {indexRes.error ? (
            <Text as="p" size="sm" tone="danger">
              Narrator linkage is unavailable; isnād names are shown as plain text.
            </Text>
          ) : null}
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
                  <p className="reader-rawtext" dir="rtl">
                    <Highlight text={pageData.text_ar} query={highlight} />
                  </p>
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
            onClose={() => {
              setRight(null);
              setNarrator(null);
            }}
          />
        ) : null}
      </div>
    </div>
  );
}
