import type { IconName } from '../../lib/design-system';
import type { NavView } from '../../lib/routes';

export type { NavView };

export interface NavItem {
  view: NavView;
  label: string;
  icon: IconName;
}

export const NAV: NavItem[] = [
  { view: 'home', label: 'Home', icon: 'compass' },
  { view: 'library', label: 'Browse', icon: 'library' },
  { view: 'daily', label: 'Daily', icon: 'daily' },
  { view: 'graph', label: 'Graph', icon: 'graph' },
];
