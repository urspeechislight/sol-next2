import type { ReactNode } from 'react';
import type { SearchScope } from '../../lib/api/client';
import { Header } from './Header';
import type { NavView } from './nav';
import './AppShell.css';

export interface AppShellProps {
  active: NavView;
  query: string;
  scope: SearchScope;
  onNav: (view: NavView) => void;
  onQuery: (q: string) => void;
  onSearch: () => void;
  onScope: (scope: SearchScope) => void;
  children: ReactNode;
}

export function AppShell({
  active,
  query,
  scope,
  onNav,
  onQuery,
  onSearch,
  onScope,
  children,
}: AppShellProps) {
  return (
    <div className="app-shell">
      <Header
        active={active}
        query={query}
        scope={scope}
        onNav={onNav}
        onQuery={onQuery}
        onSearch={onSearch}
        onScope={onScope}
      />
      <main className="app-main view">{children}</main>
    </div>
  );
}
