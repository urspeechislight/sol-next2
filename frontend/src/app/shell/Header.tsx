import { useRef, useState } from 'react';

import { Button, Icon, Input, Link, Logo, Menu, useDismiss } from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import type { SearchScope } from '../../lib/api/client';
import { viewHref } from '../../lib/routes';
import { useTheme } from '../../lib/useTheme';
import { SearchHistoryMenu } from './SearchHistoryMenu';
import { NAV, type NavView } from './nav';
import './Header.css';

// Scope -> primitive icon mapping from the design audit. Works is the one
// catalog scope: a folded works search matches titles and authors together,
// so nobody has to classify their query before typing it.
const SCOPES: MenuOption[] = [
  { value: 'content', label: 'Content', icon: 'scroll' },
  { value: 'works', label: 'Works', icon: 'book' },
  { value: 'narrator', label: 'Narrator', icon: 'network' },
  { value: 'quran', label: 'Qurʾān', icon: 'reader' },
];

const PLACEHOLDER: Record<SearchScope, string> = {
  content: 'Search book text…',
  works: 'Search works by title or author…',
  narrator: 'Search narrators…',
  quran: 'A word, or Surah:Ayah like 68:4',
};

export interface HeaderProps {
  active: NavView;
  query: string;
  scope: SearchScope;
  /** Locks the search to a contextual scope (shown read-only in the scope
      menu's slot), e.g. "this sūra" while the Qurʾān page is open. */
  scopeLock?: string;
  onNav: (view: NavView) => void;
  onQuery: (q: string) => void;
  onSearch: () => void;
  onScope: (scope: SearchScope) => void;
  onClear: () => void;
  /** A recent-searches row was picked: re-run that exact query+scope. */
  onPickHistory: (query: string, scope: SearchScope) => void;
}

export function Header({
  active,
  query,
  scope,
  scopeLock,
  onNav,
  onQuery,
  onSearch,
  onScope,
  onClear,
  onPickHistory,
}: HeaderProps) {
  const { dark, toggle: toggleTheme } = useTheme();
  const [historyOpen, setHistoryOpen] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  useDismiss(searchRef, historyOpen, () => setHistoryOpen(false));
  // The dropdown only makes sense for the global header search: while
  // scope-locked (the Qurʾān page's in-place sūra filter) or once the field
  // has text, it stays hidden.
  const showHistory = historyOpen && !scopeLock && !query.trim();

  return (
    <header className="app-header">
      <Link
        href={viewHref('home')}
        variant="default"
        className="app-brand"
        ariaLabel="SOL home"
        onActivate={() => onNav('home')}
      >
        <Logo size="sm" />
      </Link>
      <nav className="app-nav" aria-label="Primary">
        {NAV.map((item) => (
          <Button
            key={item.view}
            variant={item.view === active ? 'secondary' : 'ghost'}
            size="sm"
            iconBefore={item.icon}
            onClick={() => onNav(item.view)}
          >
            {item.label}
          </Button>
        ))}
      </nav>
      <div className="app-header__spacer" />
      <div className="app-header__search" ref={searchRef}>
        <Input
          value={query}
          type="search"
          icon="search"
          ariaLabel="Search"
          placeholder={scopeLock ? `Search ${scopeLock}…` : PLACEHOLDER[scope]}
          leading={
            <>
              {scopeLock ? (
                <span className="app-header__scope-lock">
                  <Icon name="reader" size="sm" />
                  {scopeLock}
                </span>
              ) : (
                <Menu
                  variant="bare"
                  value={scope}
                  options={SCOPES}
                  ariaLabel="Search scope"
                  onChange={(v) => onScope(v as SearchScope)}
                />
              )}
              <span className="app-header__scope-sep" aria-hidden="true" />
            </>
          }
          onInput={onQuery}
          onSubmit={onSearch}
          onClear={onClear}
          clearLabel="Clear search"
          onFocus={() => setHistoryOpen(true)}
        />
        <SearchHistoryMenu
          open={showHistory}
          scopes={SCOPES}
          onPick={(q, s) => {
            setHistoryOpen(false);
            onPickHistory(q, s);
          }}
        />
      </div>
      <Button
        variant="ghost"
        size="sm"
        iconBefore={dark ? 'sun' : 'moon'}
        ariaLabel="Toggle theme"
        onClick={toggleTheme}
      >
        {dark ? 'Light' : 'Dark'}
      </Button>
    </header>
  );
}
