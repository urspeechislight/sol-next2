// main.tsx — React mount glue. Stage 3 repoints this at ./app/App (the real shell).
import { createRoot } from "react-dom/client";
import { App } from "./App";

const container = document.getElementById("root");
if (container) {
  createRoot(container).render(<App />);
}
