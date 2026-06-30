import type { ReactNode } from 'react';
import './NarratorLink.css';

export interface NarratorLinkProps {
  active?: boolean;
  onActivate?: () => void;
  children: ReactNode;
}

/** A narrator name woven into isnād text: an inline button that opens the
    narrator. Stops propagation so it does not also trigger the enclosing unit. */
export function NarratorLink({ active, onActivate, children }: NarratorLinkProps) {
  return (
    <button
      type="button"
      className="ds-narrator-link"
      data-on={active ? '' : undefined}
      onClick={(e) => {
        e.stopPropagation();
        onActivate?.();
      }}
    >
      {children}
    </button>
  );
}
