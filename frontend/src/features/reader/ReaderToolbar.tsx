import { IconButton, Input, NavArrow, Pill, Segmented, TitleLockup } from '../../lib/design-system';
import type { IconName } from '../../lib/design-system';
import { READER } from '../../lib/constants';
import { clamp } from '../../lib/utils';

export type ReaderTheme = 'dark' | 'classical';
export type ReaderLang = 'en' | 'both' | 'ar';
export type LeftDrawer = 'contents' | null;
export type RightDrawer = 'isnad' | 'tarjama' | null;

const CHAPTER_STEP = 10;

const THEMES: [ReaderTheme, string, IconName][] = [
  ['dark', 'Dark', 'moon'],
  ['classical', 'Classical', 'book'],
];
const LANGS: [ReaderLang, string][] = [
  ['en', 'EN'],
  ['both', 'EN | AR'],
  ['ar', 'AR'],
];

function ContextRow({
  titleAr,
  titleEn,
  author,
  urn,
  lang,
  searchQuery,
  onBack,
  onSearchQuery,
}: Pick<
  ReaderToolbarProps,
  'titleAr' | 'titleEn' | 'author' | 'urn' | 'lang' | 'searchQuery' | 'onBack' | 'onSearchQuery'
>) {
  return (
    <div className="reader-toolbar__row">
      <NavArrow direction="back" surface="reader" label="Back to catalog" onClick={onBack}>
        Catalog
      </NavArrow>
      <span className="reader-vrule" />
      <div className="reader-context">
        <TitleLockup titleAr={titleAr} titleEn={titleEn} author={author} mode={lang} />
      </div>
      <Input
        surface="reader"
        className="reader-toolbar__search"
        icon="book-search"
        ariaLabel="Search in book"
        value={searchQuery}
        placeholder="ابحث في الكتاب…"
        dir="rtl"
        onInput={onSearchQuery}
      />
      <span className="reader-urn">⌗ {urn}</span>
    </div>
  );
}

function PagerRow({
  page,
  totalPages,
  onPage,
}: Pick<ReaderToolbarProps, 'page' | 'totalPages' | 'onPage'>) {
  const toPage = (n: number) => onPage(clamp(n, 1, totalPages));
  return (
    <div className="reader-toolbar__row reader-toolbar__row--pager">
      <IconButton
        surface="reader"
        label="Back ten pages"
        onClick={() => toPage(page - CHAPTER_STEP)}
      >
        «
      </IconButton>
      <IconButton
        surface="reader"
        label="Previous page"
        icon="chevron-left"
        onClick={() => toPage(page - 1)}
      />
      <Pill surface="reader" active display className="reader-pagejump">
        <span>{page.toLocaleString()}</span>
        <span className="reader-pagejump__sep">/</span>
        <span className="reader-pagejump__total">{totalPages.toLocaleString()}</span>
      </Pill>
      <IconButton
        surface="reader"
        label="Next page"
        icon="chevron-right"
        onClick={() => toPage(page + 1)}
      />
      <IconButton
        surface="reader"
        label="Forward ten pages"
        onClick={() => toPage(page + CHAPTER_STEP)}
      >
        »
      </IconButton>
    </div>
  );
}

function ThemeGroup(p: ReaderToolbarProps) {
  return (
    <div className="reader-toolbar__group">
      <Segmented
        surface="reader"
        label="Reader theme"
        value={p.readerTheme}
        options={THEMES.map(([value, label, icon]) => ({ value, label, icon }))}
        onChange={(v) => p.onTheme(v as ReaderTheme)}
      />
      <div className="reader-stepper">
        <IconButton
          surface="reader"
          size="sm"
          label="Smaller"
          onClick={() => p.onSize(p.size - READER.SIZE_STEP)}
        >
          −
        </IconButton>
        <span>{p.size}px</span>
        <IconButton
          surface="reader"
          size="sm"
          label="Larger"
          onClick={() => p.onSize(p.size + READER.SIZE_STEP)}
        >
          +
        </IconButton>
      </div>
    </div>
  );
}

function DrawerGroup(p: ReaderToolbarProps) {
  const toggleContents = () => p.onLeft(p.leftDrawer === 'contents' ? null : 'contents');
  return (
    <div className="reader-toolbar__group">
      <Segmented
        surface="reader"
        label="Language"
        value={p.lang}
        options={LANGS.map(([value, label]) => ({ value, label }))}
        onChange={(v) => p.onLang(v as ReaderLang)}
      />
      <Pill
        surface="reader"
        active={p.leftDrawer === 'contents'}
        icon="menu"
        onClick={toggleContents}
      >
        Contents
      </Pill>
      <Pill
        surface="reader"
        active={p.rightDrawer === 'isnad'}
        icon="network"
        onClick={() => p.onRight(p.rightDrawer === 'isnad' ? null : 'isnad')}
      >
        Isnād
      </Pill>
    </div>
  );
}

export interface ReaderToolbarProps {
  titleAr: string;
  titleEn?: string | null;
  author?: string | null;
  urn: string;
  page: number;
  totalPages: number;
  readerTheme: ReaderTheme;
  lang: ReaderLang;
  size: number;
  leftDrawer: LeftDrawer;
  rightDrawer: RightDrawer;
  searchQuery: string;
  onBack: () => void;
  onPage: (p: number) => void;
  onTheme: (t: ReaderTheme) => void;
  onLang: (l: ReaderLang) => void;
  onSize: (s: number) => void;
  onLeft: (d: LeftDrawer) => void;
  onRight: (d: RightDrawer) => void;
  onSearchQuery: (q: string) => void;
}

export function ReaderToolbar(p: ReaderToolbarProps) {
  return (
    <header className="reader-toolbar">
      <ContextRow
        titleAr={p.titleAr}
        titleEn={p.titleEn}
        author={p.author}
        urn={p.urn}
        lang={p.lang}
        searchQuery={p.searchQuery}
        onBack={p.onBack}
        onSearchQuery={p.onSearchQuery}
      />
      <PagerRow page={p.page} totalPages={p.totalPages} onPage={p.onPage} />
      <div className="reader-toolbar__row reader-toolbar__row--settings">
        <ThemeGroup {...p} />
        <DrawerGroup {...p} />
      </div>
    </header>
  );
}
