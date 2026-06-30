import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

import { API } from './src/lib/routes';

// Dev server binds all interfaces so the laptop can reach buildhost's Vite.
// The API prefix is proxied to the FastAPI backend on :8001 — the data
// linkage. The typed client in src/lib/api fetches relative API paths
// (mirroring sol-next's vite proxy), so no CORS rules or hardcoded host
// leak into the app. The prefix itself comes from routes.ts (CENTRAL-006).
const API_TARGET = 'http://localhost:8001';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      [API.BASE]: { target: API_TARGET, changeOrigin: true },
    },
  },
  // Unit tests for pure lib logic (Arabic folding, highlight, utils). Node
  // environment: these are DOM-free pure functions. Co-located *.test.ts.
  test: {
    environment: 'node',
    include: ['src/**/*.test.ts'],
  },
});
