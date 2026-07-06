import type { ReactNode } from 'react';
import { Header } from './Header';
import type { HeaderProps } from './Header';
import './AppShell.css';

/** The shell is the header plus a content slot: its props ARE the header's
    (single definition in Header.tsx) with children added. */
export interface AppShellProps extends HeaderProps {
  children: ReactNode;
}

export function AppShell({ children, ...header }: AppShellProps) {
  return (
    <div className="app-shell">
      <Header {...header} />
      <main className="app-main view">{children}</main>
    </div>
  );
}
