import type { ReactNode } from "react";
import { Header } from "./Header";
import type { NavView } from "./nav";
import "./AppShell.css";

export interface AppShellProps {
  active: NavView;
  query: string;
  onNav: (view: NavView) => void;
  onQuery: (q: string) => void;
  children: ReactNode;
}

export function AppShell({ active, query, onNav, onQuery, children }: AppShellProps) {
  return (
    <div className="app-shell">
      <Header active={active} query={query} onNav={onNav} onQuery={onQuery} />
      <main className="app-main view">{children}</main>
    </div>
  );
}
