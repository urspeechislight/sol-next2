import { useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties } from 'react';

import { Spinner, Text } from '../../lib/design-system';
import {
  getBook,
  getBookVolumes,
  getNarratorEntry,
  getPage,
  getPageCitations,
  getToc,
  isNotFound,
  searchBook,
} from '../../lib/api/client';
import { READER } from '../../lib/constants';
import { matchedMarkers } from '../../lib/footnotes';
import { useTheme } from '../../lib/useTheme';
import { buildNarratorIndex, narratorToRecord } from '../../lib/narrators';
import { emptyPage } from '../../lib/types';
import type {
  Book,
  BookPage,
  BookSearchMatch,
  Narrator,
  NarratorRecord,
  Page,
  QuranCitation,
} from '../../lib/types';
import { useAsync } from '../../lib/useAsync';
import { useDomains } from '../../lib/useDomains';
import { clamp, deathLabel } from '../../lib/utils';
import { HadithUnit, UNIT_NOUN_DEFAULT, UNIT_NOUNS } from './HadithUnit';
import { PageFootnotes, pulseFootnoteTarget } from './PageFootnotes';
import { MatchList, TocDrawer } from './ReaderDrawers';
import { IsnadPanel, TarjamaPanel } from './ReaderPanels';
import type { NarratorFetchError } from './ReaderPanels';
import { RawPageText } from './RawPageText';
import { ReaderToolbar } from './ReaderToolbar';
import type { LeftDrawer, ReaderLang, ReaderTheme, RightDrawer } from './ReaderToolbar';
import './reader.css';
import '../../components/HadithBlock.css';
import './IsnadSidebar.css';
import './NarratorTarjama.css';

const MIN_QUERY = 2;
const EMPTY_MATCHES = emptyPage<BookSearchMatch>();
const NO_MARKERS: ReadonlySet<string> = new Set<string>();
const EMPTY_CITATIONS: QuranCitation[] = [];

/** Promote a served narrator to a registry-shaped record. A linked narrator
    carries its registry narrator_id (resolved at build time); the click
    handler then fetches the full biography. An unlinked one shows name-only
    (id -1). The served grade is the extraction's English verdict; it stands
    in for the tier until the registry detail replaces it. */
function recordFromNarrator(n: Narrator): NarratorRecord {
  return {
    id: n.narrator_id ?? -1,
    narrator_id: n.narrator_id,
    primary_name_ar: n.name_ar || n.name,
    primary_name_en: n.name,
    kunya: '',
    nisba: '',
    tradition: '',
    birth_year_ah: null,
    death_year_ah: n.d,
    death_year_ce: '',
    teacher_count: 0,
    student_count: 0,
    tier: n.grade || null,
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

/** A transient fetch fault (network, backend outage). Distinct from
    `Unavailable`: the page may well exist — the request simply failed. */
function LoadError() {
  return (
    <div className="reader-unavailable">
      <Text as="p" size="lg" font="serif">
        Could not load this page
      </Text>
      <Text as="p" size="sm" tone="muted">
        The corpus service did not respond. Check the connection and try again.
      </Text>
    </div>
  );
}

export interface ReaderScreenProps {
  urn: string;
  page: number;
  initialQuery?: string;
  onPage: (page: number) => void;
  /** Open a sibling volume of the same work (from the masthead's volume menu). */
  onVolume: (urn: string) => void;
  /** Open the Qurʾān reader focused on a verse (from an in-text citation link). */
  onCite: (surah: number, aya: number) => void;
  onBack: () => void;
}

export function ReaderScreen({
  urn,
  page,
  initialQuery = '',
  onPage,
  onVolume,
  onCite,
  onBack,
}: ReaderScreenProps) {
  const { dark } = useTheme();
  const [readerTheme, setReaderTheme] = useState<ReaderTheme>(dark ? 'dark' : 'classical');
  const [lang, setLang] = useState<ReaderLang>('both');
  const [size, setSize] = useState<number>(READER.SIZE_DEFAULT);
  const [left, setLeft] = useState<LeftDrawer>('contents');
  const [right, setRight] = useState<RightDrawer>(null);
  const [activeHadith, setActiveHadith] = useState(0);
  const [cards, setCards] = useState(true);
  const [narrator, setNarrator] = useState<NarratorRecord | null>(null);
  const [narratorError, setNarratorError] = useState<NarratorFetchError | null>(null);
  const [searchQ, setSearchQ] = useState(initialQuery);
  const articleRef = useRef<HTMLElement | null>(null);

  // App (and the URL) own the page; reset the in-page highlight when it changes.
  useEffect(() => {
    setActiveHadith(0);
  }, [page]);

  const bookRes = useAsync(() => getBook(urn), [urn]);
  const volumesRes = useAsync<Book[]>(() => getBookVolumes(urn), [urn]);
  const tocRes = useAsync(() => getToc(urn), [urn]);
  const domainsRes = useDomains();
  const pageRes = useAsync<BookPage>(() => getPage(urn, page), [urn, page]);
  const citationsRes = useAsync<QuranCitation[]>(() => getPageCitations(urn, page), [urn, page]);
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
  // Category slugs -> human labels + owning domain, from the taxonomy; the
  // masthead badge shows the label ("Arabic Language Sciences"), never the raw
  // slug, and the domain picks the unit noun the cards carry.
  const taxonomy = useMemo(() => {
    const labels = new Map<string, string>();
    const domains = new Map<string, string>();
    for (const domain of domainsRes.data ?? []) {
      for (const category of domain.categories) {
        labels.set(category.slug, category.label);
        domains.set(category.slug, domain.id);
      }
    }
    return { labels, domains };
  }, [domainsRes.data]);

  // The page's numbered apparatus entries gate the marker tokenizer; the
  // markers actually found in the body decide which entries link back.
  const entryMarkers = useMemo(() => {
    const numbered = (pageRes.data?.footnotes ?? [])
      .map((f) => f.marker)
      .filter((m): m is string => m !== null);
    return numbered.length > 0 ? new Set(numbered) : NO_MARKERS;
  }, [pageRes.data]);
  const linkedMarkers = useMemo(
    () => (pageRes.data?.text_ar ? matchedMarkers(pageRes.data.text_ar, entryMarkers) : NO_MARKERS),
    [pageRes.data, entryMarkers],
  );
  const jumpToEntry = (marker: string) =>
    pulseFootnoteTarget(articleRef.current, `[data-fn-entry="${marker}"]`);
  const jumpToMarker = (marker: string) =>
    pulseFootnoteTarget(articleRef.current, `[data-fn-ref="${marker}"]`);

  const openRecord = (record: NarratorRecord) => {
    setNarrator(record);
    setNarratorError(null);
    setRight('tarjama');
    if (record.id < 0) return;
    getNarratorEntry(record.id)
      .then(narratorToRecord)
      .then((full) =>
        setNarrator((current) => (current && current.id === record.id ? full : current)),
      )
      .catch((err: unknown) =>
        setNarratorError({
          id: record.id,
          message: err instanceof Error ? err.message : String(err),
        }),
      );
  };
  const openNarrator = (n: Narrator) => openRecord(recordFromNarrator(n));
  const rootStyle = { '--reader-size': `${size}px` } as CSSProperties;

  const book = bookRes.data;
  const categoryLabel = book ? taxonomy.labels.get(book.category) : undefined;
  const bookDomain = book ? taxonomy.domains.get(book.category) : undefined;
  const unitNoun = UNIT_NOUNS[bookDomain ?? ''] ?? UNIT_NOUN_DEFAULT;
  const volume = book?.volume ?? null;
  const death = deathLabel(book?.death_year_ah) || null;
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
        urn={urn}
        volumes={volumesRes.data}
        onVolume={onVolume}
        page={page}
        totalPages={totalPages}
        readerTheme={readerTheme}
        lang={lang}
        size={size}
        leftDrawer={left}
        rightDrawer={right}
        cards={cards}
        onCards={() => setCards((c) => !c)}
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
          {pageRes.error ? (
            isNotFound(pageRes.error) ? (
              <Unavailable title={title} />
            ) : (
              <LoadError />
            )
          ) : null}
          {pageData ? (
            <article className="reader-article" data-cards={cards ? 'on' : 'off'} ref={articleRef}>
              <PageHead page={pageData} />
              <div>
                {hadiths.length > 0 ? (
                  hadiths.map((h, i) => (
                    <HadithUnit
                      key={h.n}
                      h={h}
                      noun={unitNoun}
                      active={i === activeHadith}
                      lang={lang}
                      index={index}
                      activeNarrator={narrator?.primary_name_ar ?? ''}
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
                    markers={entryMarkers}
                    onMarker={jumpToEntry}
                    citations={citationsRes.data ?? EMPTY_CITATIONS}
                    onCite={onCite}
                  />
                ) : null}
              </div>
              <PageFootnotes
                footnotes={pageData.footnotes}
                linked={lang === 'en' ? NO_MARKERS : linkedMarkers}
                lang={lang}
                onBacklink={jumpToMarker}
              />
            </article>
          ) : null}
        </main>
        {right === 'isnad' && active ? (
          <IsnadPanel hadith={active} onNarrator={openNarrator} />
        ) : null}
        {right === 'tarjama' && narrator ? (
          <TarjamaPanel
            record={narrator}
            error={narratorError && narratorError.id === narrator.id ? narratorError.message : null}
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
