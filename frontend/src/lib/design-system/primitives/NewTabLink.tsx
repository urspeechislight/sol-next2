import { cx } from '../../utils';
import { Icon } from './Icon';
import './NewTabLink.css';

export interface NewTabLinkProps {
  href: string;
  /** Accessible name (the control is icon-only), e.g. "Open Bihar al-Anwar
      at vol. 6, p. 318 in a new tab". */
  label: string;
  className?: string;
}

/** THE canonical "open in a new tab" control: a real, icon-only anchor
    (right-click "copy link address" and middle-click both work, unlike a
    button that calls window.open), always target=_blank with the safe rel.
    The one place the open-in-new-tab glyph is drawn, so every call site —
    today the search results' passage rows, anywhere else later — gets the
    same icon for free instead of hand-rolling its own. */
export function NewTabLink({ href, label, className }: NewTabLinkProps) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer noopener"
      aria-label={label}
      className={cx('ds-newtab', className)}
    >
      <Icon name="external" size="sm" />
    </a>
  );
}
