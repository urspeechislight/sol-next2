import { Highlight } from '../primitives/Highlight';
import './MatchRow.css';

export interface MatchRowProps {
  page: number;
  snippet: string;
  query: string;
  onClick?: () => void;
}

/** Reader in-book search result: a page label plus the highlighted snippet. */
export function MatchRow({ page, snippet, query, onClick }: MatchRowProps) {
  return (
    <button type="button" className="ds-matchrow" onClick={onClick}>
      <div className="ds-matchrow__pg">page {page}</div>
      <div className="ds-matchrow__ar" dir="rtl">
        <Highlight text={snippet} query={query} />
      </div>
    </button>
  );
}
