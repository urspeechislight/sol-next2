import './TocItem.css';

export interface TocItemProps {
  titleAr: string;
  titleEn?: string | null;
  page: number;
  current?: boolean;
  onClick?: () => void;
}

/** Reader table-of-contents entry: a selectable row on the reading surface. */
export function TocItem({ titleAr, titleEn, page, current, onClick }: TocItemProps) {
  return (
    <button
      type="button"
      className="ds-tocitem"
      aria-current={current || undefined}
      onClick={onClick}
    >
      <span>
        <span className="ds-tocitem__ar" dir="rtl">
          {titleAr}
        </span>
        {titleEn ? <span className="ds-tocitem__en">{titleEn}</span> : null}
      </span>
      <span className="ds-tocitem__pg">{page}</span>
    </button>
  );
}
