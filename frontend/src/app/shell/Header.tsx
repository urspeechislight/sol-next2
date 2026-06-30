import { useState } from 'react';
import { Button, Input, Link, Logo, Menu } from '../../lib/design-system';
import type { MenuOption } from '../../lib/design-system';
import type { SearchScope } from '../../lib/api/client';
import { THEME } from '../../lib/constants';
import { viewHref } from '../../lib/routes';
import { NAV, type NavView } from './nav';
import './Header.css';

// Scope -> primitive icon mapping from the design audit.
const SCOPES: MenuOption[] = [
  { value: 'content', label: 'Content', icon: 'scroll' },
  { value: 'title', label: 'Title', icon: 'type' },
  { value: 'author', label: 'Author', icon: 'users' },
  { value: 'book', label: 'Book', icon: 'book' },
  { value: 'narrator', label: 'Narrator', icon: 'network' },
  { value: 'quran', label: 'Qurʾān', icon: 'reader' },
];

const PLACEHOLDER: Record<SearchScope, string> = {
  content: 'Search book text…',
  title: 'Search titles…',
  author: 'Search authors…',
  book: 'Search books…',
  narrator: 'Search narrators…',
  quran: 'A word, or Surah:Ayah like 68:4',
};

export interface HeaderProps {
  active: NavView;
  query: string;
  scope: SearchScope;
  onNav: (view: NavView) => void;
  onQuery: (q: string) => void;
  onSearch: () => void;
  onScope: (scope: SearchScope) => void;
}

export function Header({ active, query, scope, onNav, onQuery, onSearch, onScope }: HeaderProps) {
  const [dark, setDark] = useState(false);
  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute(THEME.ATTR, next ? THEME.DARK : THEME.LIGHT);
  };
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
      <div className="app-header__search">
        <Input
          value={query}
          type="search"
          icon="search"
          ariaLabel="Search"
          placeholder={PLACEHOLDER[scope]}
          leading={
            <>
              <Menu
                variant="bare"
                value={scope}
                options={SCOPES}
                ariaLabel="Search scope"
                onChange={(v) => onScope(v as SearchScope)}
              />
              <span className="app-header__scope-sep" aria-hidden="true" />
            </>
          }
          onInput={onQuery}
          onSubmit={onSearch}
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
