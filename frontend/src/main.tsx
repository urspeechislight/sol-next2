// main.tsx — React mount glue. Mounts the SOL app (home / library / daily / graph).
// Fonts are self-hosted via @fontsource (the same families+weights index.html
// once pulled from Google Fonts): the app renders with zero CDN dependency.
import '@fontsource/newsreader/400.css';
import '@fontsource/newsreader/400-italic.css';
import '@fontsource/newsreader/500.css';
import '@fontsource/newsreader/600.css';
import '@fontsource/scheherazade-new/400.css';
import '@fontsource/scheherazade-new/500.css';
import '@fontsource/scheherazade-new/600.css';
import '@fontsource/scheherazade-new/700.css';
import '@fontsource/amiri/400.css';
import '@fontsource/amiri/400-italic.css';
import '@fontsource/amiri/700.css';
import '@fontsource/noto-naskh-arabic/400.css';
import '@fontsource/noto-naskh-arabic/500.css';
import '@fontsource/noto-naskh-arabic/700.css';
import '@fontsource/ibm-plex-sans/400.css';
import '@fontsource/ibm-plex-sans/500.css';
import '@fontsource/ibm-plex-sans/600.css';
import '@fontsource/ibm-plex-mono/400.css';
import '@fontsource/ibm-plex-mono/500.css';
import '@fontsource/ibm-plex-mono/600.css';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';

const container = document.getElementById('root');
if (container) {
  createRoot(container).render(<App />);
}
