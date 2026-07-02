// main.tsx — React mount glue. Mounts the SOL app (home / library / daily / graph).
import { createRoot } from 'react-dom/client';
import { App } from './app/App';

const container = document.getElementById('root');
if (container) {
  createRoot(container).render(<App />);
}
