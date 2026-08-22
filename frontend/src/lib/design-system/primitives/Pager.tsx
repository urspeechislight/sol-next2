import { cx, pageWindow } from '../../utils';
import { Button } from './Button';
import './Pager.css';

// Max number-buttons shown around the current page.
const PAGE_WINDOW = 5;

export interface PagerProps {
  page: number;
  totalPages: number;
  onPage: (page: number) => void;
  className?: string;
}

export function Pager({ page, totalPages, onPage, className }: PagerProps) {
  if (totalPages <= 1) return null;
  const window = pageWindow(page, totalPages, PAGE_WINDOW);
  return (
    <nav className={cx('ds-pager', className)} aria-label="Pagination">
      <Button
        variant="ghost"
        size="sm"
        iconBefore="chevron-left"
        ariaLabel="Previous page"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      />
      {(window[0] ?? 0) > 1 ? <span className="ds-pager__gap">…</span> : null}
      {window.map((p) => (
        <button
          key={p}
          type="button"
          aria-current={p === page}
          className={cx('ds-pager__page', p === page && 'ds-pager__page--on')}
          onClick={() => onPage(p)}
        >
          {p}
        </button>
      ))}
      {(window[window.length - 1] ?? page) < totalPages ? (
        <span className="ds-pager__gap">…</span>
      ) : null}
      <Button
        variant="ghost"
        size="sm"
        iconBefore="chevron-right"
        ariaLabel="Next page"
        disabled={page >= totalPages}
        onClick={() => onPage(page + 1)}
      />
    </nav>
  );
}
