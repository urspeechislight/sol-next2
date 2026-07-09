import {
  Icon,
  IconButton,
  Input,
  Menu,
  NavArrow,
  Pill,
  Segmented,
  TitleLockup,
} from '../../lib/design-system';
import type { IconName, LockupMode } from '../../lib/design-system';
import { LANG_OPTIONS, READER } from '../../lib/constants';
import type { Book } from '../../lib/types';
import { clamp, formatCount } from '../../lib/utils';

export type ReaderTheme = 'dark' | 'classical';
export type ReaderLang = LockupMode;
export type LeftDrawer = 'contents' | null;
export type RightDrawer = 'isnad' | 'tarjama' | null;

const CHAPTER_STEP = 10;

const THEMES: [ReaderTheme, string, IconName][] = [
  ['dark', 'Dark', 'moon'],
  ['classical', 'Classical', 'book'],
];

/** Option label for one sibling volume. Every multi-volume work in the corpus
    numbers its volumes; if one ever arrives unnumbered, its URN is shown so
    the row stays true and unique rather than claiming a made-up number. */
function volumeOptionLabel(book: Book): string {
  return book.volume === null ? book.urn : `Volume ${book.volume}`;
}

function ReaderMeta({
  categoryLabel,
  volume,
  death,
  urn,
  volumes,
  onVolume,
}: Pick<
  ReaderToolbarProps,
  'categoryLabel' | 'volume' | 'death' | 'urn' | 'volumes' | 'onVolume'
>) {
  if (!categoryLabel && !volume && !death) return null;
  return (
    <div className="reader-meta">
      {categoryLabel ? (
        <span className="reader-badge reader-badge--cat">
          <Icon name="layers" size="sm" />
          {categoryLabel}
        </span>
      ) : null}
      {death ? <span className="reader-badge">{death}</span> : null}
      {volumes !== null && volumes.length > 1 ? (
        <Menu
          surface="reader"
          className="reader-badge-menu"
          ariaLabel="Switch volume"
          value={urn}
          options={volumes.map((b) => ({
            value: b.urn,
            label: volumeOptionLabel(b),
            icon: 'book' as const,
          }))}
          onChange={onVolume}
        />
      ) : volume ? (
        <span className="reader-badge reader-badge--vol">
          <Icon name="book" size="sm" />
          Volume {volume}
        </span>
      ) : null}
    </div>
  );
}

function ContextRow({
  titleAr,
  titleEn,
  author,
  lang,
  searchQuery,
  categoryLabel,
  volume,
  death,
  urn,
  volumes,
  onVolume,
  onBack,
  onSearchQuery,
  onClearSearch,
}: Pick<
  ReaderToolbarProps,
  | 'titleAr'
  | 'titleEn'
  | 'author'
  | 'lang'
  | 'searchQuery'
  | 'categoryLabel'
  | 'volume'
  | 'death'
  | 'urn'
  | 'volumes'
  | 'onVolume'
  | 'onBack'
  | 'onSearchQuery'
  | 'onClearSearch'
>) {
  return (
    <div className="reader-toolbar__row reader-toolbar__row--context">
      <NavArrow direction="back" surface="reader" label="Back to catalog" onClick={onBack}>
        Catalog
      </NavArrow>
      <span className="reader-vrule" />
      <div className="reader-context">
        <div className="reader-masthead">
          <TitleLockup
            variant="editorial"
            titleAr={titleAr}
            titleEn={titleEn}
            author={author}
            mode={lang}
          />
          <ReaderMeta
            categoryLabel={categoryLabel}
            volume={volume}
            death={death}
            urn={urn}
            volumes={volumes}
            onVolume={onVolume}
          />
        </div>
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
        onClear={onClearSearch}
        clearLabel="Clear search"
      />
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
        <span>{formatCount(page)}</span>
        <span className="reader-pagejump__sep">/</span>
        <span className="reader-pagejump__total">{formatCount(totalPages)}</span>
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
        options={LANG_OPTIONS}
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
      <Pill surface="reader" active={p.cards} icon="grid" onClick={p.onCards}>
        Cards
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
  /** Human-readable category label (e.g. "Arabic Language Sciences"). */
  categoryLabel?: string | null;
  /** Volume number for a multi-volume work; omitted for single-volume books. */
  volume?: number | null;
  /** Pre-formatted death label, e.g. "d. 732 AH". */
  death?: string | null;
  /** URN of the open book: the volume menu's current value. */
  urn: string;
  /** Every volume of the open work, ascending (null while loading). The
      volume badge becomes a switcher menu when there is more than one. */
  volumes: Book[] | null;
  onVolume: (urn: string) => void;
  page: number;
  totalPages: number;
  readerTheme: ReaderTheme;
  lang: ReaderLang;
  size: number;
  leftDrawer: LeftDrawer;
  rightDrawer: RightDrawer;
  /** Card view: framed reading units when on, continuous text when off. */
  cards: boolean;
  onCards: () => void;
  searchQuery: string;
  onBack: () => void;
  onPage: (p: number) => void;
  onTheme: (t: ReaderTheme) => void;
  onLang: (l: ReaderLang) => void;
  onSize: (s: number) => void;
  onLeft: (d: LeftDrawer) => void;
  onRight: (d: RightDrawer) => void;
  onSearchQuery: (q: string) => void;
  onClearSearch: () => void;
}

export function ReaderToolbar(p: ReaderToolbarProps) {
  return (
    <header className="reader-toolbar">
      <ContextRow
        titleAr={p.titleAr}
        titleEn={p.titleEn}
        author={p.author}
        categoryLabel={p.categoryLabel}
        volume={p.volume}
        death={p.death}
        urn={p.urn}
        volumes={p.volumes}
        onVolume={p.onVolume}
        lang={p.lang}
        searchQuery={p.searchQuery}
        onBack={p.onBack}
        onSearchQuery={p.onSearchQuery}
        onClearSearch={p.onClearSearch}
      />
      <PagerRow page={p.page} totalPages={p.totalPages} onPage={p.onPage} />
      <div className="reader-toolbar__row reader-toolbar__row--settings">
        <ThemeGroup {...p} />
        <DrawerGroup {...p} />
      </div>
    </header>
  );
}
