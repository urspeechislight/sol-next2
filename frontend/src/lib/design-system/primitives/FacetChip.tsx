import type { ReactNode } from 'react';
import { formatCount } from '../../utils';
import { UnstyledButton } from './UnstyledButton';
import './FacetChip.css';

export interface FacetChipProps {
  label: ReactNode;
  /** True facet count; omit for pure toggles (e.g. the foundational filter). */
  count?: number;
  on: boolean;
  /** Group chips only: some but not all of the group's members are selected. */
  partial?: boolean;
  onToggle: () => void;
  ariaLabel?: string;
}

/** The one toggleable facet token: a label with an optional mono count,
    pressed state in the accent tint, and a half-pressed state for a group
    whose members are partially selected. The single chip grammar for every
    count-bearing filter (the library's era chips, the search distribution
    map); its removable sibling is Chip. */
export function FacetChip({
  label,
  count,
  on,
  partial = false,
  onToggle,
  ariaLabel,
}: FacetChipProps) {
  const cls = on ? 'ds-fchip ds-fchip--on' : partial ? 'ds-fchip ds-fchip--part' : 'ds-fchip';
  return (
    <UnstyledButton
      className={cls}
      onClick={onToggle}
      ariaPressed={on ? true : partial ? 'mixed' : false}
      ariaLabel={ariaLabel}
    >
      <span className="ds-fchip__label">{label}</span>
      {count !== undefined ? <span className="ds-fchip__n">{formatCount(count)}</span> : null}
    </UnstyledButton>
  );
}
