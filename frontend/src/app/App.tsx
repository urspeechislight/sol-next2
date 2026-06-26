import { useState } from "react";
import { AppShell } from "./shell/AppShell";
import type { NavView } from "./shell/nav";
import { HomeScreen } from "../features/home/HomeScreen";
import { LibraryScreen } from "../features/library/LibraryScreen";
import { DailyScreen } from "../features/daily/DailyScreen";
import { GraphScreen } from "../features/graph/GraphScreen";
import "../lib/design-system/tokens.css";
import "../lib/design-system/base.css";

/** State-based router for the SOL workbench (home / library / daily / graph). */
export function App() {
  const [view, setView] = useState<NavView>("home");
  const [query, setQuery] = useState("");

  // The immersive Reader is the next stage; the reader affordances are present
  // but inert until ReaderScreen lands.
  const openReader = () => {};

  return (
    <AppShell active={view} query={query} onNav={setView} onQuery={setQuery}>
      {view === "home" ? <HomeScreen onNav={setView} onOpenReader={openReader} /> : null}
      {view === "library" ? <LibraryScreen onOpenReader={openReader} /> : null}
      {view === "daily" ? <DailyScreen onOpenReader={openReader} /> : null}
      {view === "graph" ? <GraphScreen /> : null}
    </AppShell>
  );
}
