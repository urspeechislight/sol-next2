import type { IconName } from '../../lib/design-system';
import type { NavView } from '../../lib/routes';

export type { NavView };

// The visible nav: Browse leads (the library is the front door's primary
// action), and the landing page needs no menu item because the logo and '/'
// already point at it. 'home' and 'design' stay valid routes (routes.ts owns
// the full set); this list is only what the header shows. Extraction is the
// knowledge-graph extraction inspector; it needs the backend's SOL_DEV_TOOLS
// opt-in, and without it the screen states that the dev API is off.
export const NAV: NavItem[] = [
  { view: 'library', label: 'Browse', icon: 'library' },
  { view: 'quran', label: 'Qurʾān', icon: 'book' },
  { view: 'graph', label: 'Graph', icon: 'graph' },
  { view: 'extraction', label: 'Extraction', icon: 'layers' },
];

export interface NavItem {
  view: NavView;
  label: string;
  icon: IconName;
}
