import type { IconName } from '../../lib/design-system';
import type { NavView } from '../../lib/routes';

export type { NavView };

export interface NavItem {
  view: NavView;
  label: string;
  icon: IconName;
}

export const NAV: NavItem[] = [
  { view: 'home', label: 'Today', icon: 'daily' },
  { view: 'library', label: 'Browse', icon: 'library' },
  { view: 'quran', label: 'Qurʾān', icon: 'book' },
  { view: 'graph', label: 'Graph', icon: 'graph' },
];
