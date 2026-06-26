// main.tsx:React mount glue. Stage 1 mounts the design-system preview;
// Stage 3 repoints this at ./app/App (the real shell).
import { createRoot } from 'react-dom/client';
import { DesignSystem } from './preview/DesignSystem';

const container = document.getElementById('root');
if (container) {
  createRoot(container).render(<DesignSystem />);
}
