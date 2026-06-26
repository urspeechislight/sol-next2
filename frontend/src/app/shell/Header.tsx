import { useState } from "react";
import { Button, Input, Link, Logo } from "../../lib/design-system";
import { THEME } from "../../lib/constants";
import { NAV, type NavView } from "./nav";
import "./Header.css";

export interface HeaderProps {
  active: NavView;
  query: string;
  onNav: (view: NavView) => void;
  onQuery: (q: string) => void;
}

export function Header({ active, query, onNav, onQuery }: HeaderProps) {
  const [dark, setDark] = useState(false);
  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute(THEME.ATTR, next ? THEME.DARK : THEME.LIGHT);
  };
  return (
    <header className="app-header">
      <Link href="#home" variant="default" className="app-brand" ariaLabel="SOL home" onActivate={() => onNav("home")}>
        <Logo size="sm" />
      </Link>
      <nav className="app-nav" aria-label="Primary">
        {NAV.map((item) => (
          <Button
            key={item.view}
            variant={item.view === active ? "secondary" : "ghost"}
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
        <Input value={query} icon="search" type="search" ariaLabel="Search" placeholder="Search books, narrators…" onInput={onQuery} />
      </div>
      <Button variant="ghost" size="sm" iconBefore={dark ? "sun" : "moon"} ariaLabel="Toggle theme" onClick={toggleTheme}>
        {dark ? "Light" : "Dark"}
      </Button>
    </header>
  );
}
