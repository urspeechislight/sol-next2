import type { IconName } from '../../lib/design-system';
import type { NavView } from '../../lib/routes';

export type { NavView };

// The visible nav: Browse leads (the library is the front door's primary
// action), and the landing page needs no menu item because the logo and '/'
// already point at it. 'home' and 'design' stay valid routes (routes.ts owns
// the full set); this list is only what the header shows.
export const NAV: NavItem[] = [
  { view: 'library', label: 'Browse', icon: 'library' },
  { view: 'quran', label: 'Qurʾān', icon: 'book' },
  { view: 'graph', label: 'Graph', icon: 'graph' },
];

export interface NavItem {
  view: NavView;
  label: string;
  icon: IconName;
}
