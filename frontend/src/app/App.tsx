import { useState } from "react";
import { AppShell } from "./shell/AppShell";
import type { NavView } from "./shell/nav";
import { HomeScreen } from "../features/home/HomeScreen";
import { LibraryScreen } from "../features/library/LibraryScreen";
import { DailyScreen } from "../features/daily/DailyScreen";
import { GraphScreen } from "../features/graph/GraphScreen";
import { ReaderScreen } from "../features/reader/ReaderScreen";
import "../lib/design-system/tokens.css";
import "../lib/design-system/base.css";

/** State-based router for the SOL workbench. The Reader is a full-screen
    takeover (no app shell). */
export function App() {
  const [view, setView] = useState<NavView>("home");
  const [query, setQuery] = useState("");
  const [reading, setReading] = useState(false);

  if (reading) return <ReaderScreen onBack={() => setReading(false)} />;

  const openReader = () => setReading(true);

  return (
    <AppShell active={view} query={query} onNav={setView} onQuery={setQuery}>
      {view === "home" ? <HomeScreen onNav={setView} onOpenReader={openReader} /> : null}
      {view === "library" ? <LibraryScreen onOpenReader={openReader} /> : null}
      {view === "daily" ? <DailyScreen onOpenReader={openReader} /> : null}
      {view === "graph" ? <GraphScreen /> : null}
    </AppShell>
  );
}
