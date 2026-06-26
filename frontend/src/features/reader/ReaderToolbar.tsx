import { Icon } from "../../lib/design-system";
import type { IconName } from "../../lib/design-system";

export type ReaderTheme = "bright" | "dark" | "classical";
export type ReaderLang = "en" | "both" | "ar";
export type LeftDrawer = "contents" | "search" | null;
export type RightDrawer = "isnad" | "tarjama" | null;

const THEMES: [ReaderTheme, string, IconName][] = [
  ["bright", "Bright", "sun"], ["dark", "Dark", "moon"], ["classical", "Classical", "book"],
];
const LANGS: [ReaderLang, string][] = [["en", "EN"], ["both", "EN | AR"], ["ar", "AR"]];

export interface ReaderToolbarProps {
  page: number;
  totalPages: number;
  readerTheme: ReaderTheme;
  lang: ReaderLang;
  size: number;
  leftDrawer: LeftDrawer;
  rightDrawer: RightDrawer;
  onBack: () => void;
  onPage: (p: number) => void;
  onTheme: (t: ReaderTheme) => void;
  onLang: (l: ReaderLang) => void;
  onSize: (s: number) => void;
  onLeft: (d: LeftDrawer) => void;
  onRight: (d: RightDrawer) => void;
}

export function ReaderToolbar(p: ReaderToolbarProps) {
  const pill = (on: boolean) => `reader-pill${on ? " reader-pill--on" : ""}`;
  return (
    <header className="reader-toolbar">
      <div className="reader-toolbar__row">
        <button className="reader-pill" type="button" onClick={p.onBack}><Icon name="arrow-left" size="sm" /> Catalog</button>
        <span className="reader-vrule" />
        <div className="reader-context">
          <span className="reader-title-ar" dir="rtl">وسائل الشيعة</span>
          <span className="reader-context__en">· Wasāʾil al-Shīʿa · al-Ḥurr al-ʿĀmilī</span>
        </div>
        <span className="reader-urn">urn:WasShia</span>
      </div>
      <div className="reader-toolbar__row reader-toolbar__row--pager">
        <button className="reader-iconbtn" aria-label="Previous chapter" onClick={() => p.onPage(Math.max(1, p.page - 10))}>«</button>
        <button className="reader-iconbtn" aria-label="Previous page" onClick={() => p.onPage(Math.max(1, p.page - 1))}><Icon name="chevron-left" size="sm" /></button>
        <span className="reader-pill reader-pill--on reader-pagejump">
          <span>{p.page.toLocaleString()}</span>
          <span className="reader-pagejump__sep">/</span>
          <span className="reader-pagejump__total">{p.totalPages.toLocaleString()}</span>
        </span>
        <button className="reader-iconbtn" aria-label="Next page" onClick={() => p.onPage(Math.min(p.totalPages, p.page + 1))}><Icon name="chevron-right" size="sm" /></button>
        <button className="reader-iconbtn" aria-label="Next chapter" onClick={() => p.onPage(Math.min(p.totalPages, p.page + 10))}>»</button>
      </div>
      <div className="reader-toolbar__row reader-toolbar__row--settings">
        <div className="reader-toolbar__group">
          <div className="reader-seg" role="radiogroup" aria-label="Reader theme">
            {THEMES.map(([v, label, icon]) => (
              <button key={v} className="reader-seg__btn" aria-pressed={p.readerTheme === v} onClick={() => p.onTheme(v)}>
                <Icon name={icon} size="sm" />{label}
              </button>
            ))}
          </div>
          <div className="reader-stepper">
            <button className="reader-iconbtn reader-iconbtn--sm" aria-label="Smaller" onClick={() => p.onSize(p.size - 1)}>−</button>
            <span>{p.size}px</span>
            <button className="reader-iconbtn reader-iconbtn--sm" aria-label="Larger" onClick={() => p.onSize(p.size + 1)}>+</button>
          </div>
        </div>
        <div className="reader-toolbar__group">
          <div className="reader-seg" role="radiogroup" aria-label="Language">
            {LANGS.map(([v, label]) => (
              <button key={v} className="reader-seg__btn" aria-pressed={p.lang === v} onClick={() => p.onLang(v)}>{label}</button>
            ))}
          </div>
          <button className={pill(p.leftDrawer === "contents")} onClick={() => p.onLeft(p.leftDrawer === "contents" ? null : "contents")}><Icon name="menu" size="sm" /> Contents</button>
          <button className={pill(p.leftDrawer === "search")} onClick={() => p.onLeft(p.leftDrawer === "search" ? null : "search")}><Icon name="search" size="sm" /> Search</button>
          <button className={pill(p.rightDrawer === "isnad")} onClick={() => p.onRight(p.rightDrawer === "isnad" ? null : "isnad")}><Icon name="network" size="sm" /> Isnād</button>
        </div>
      </div>
    </header>
  );
}
