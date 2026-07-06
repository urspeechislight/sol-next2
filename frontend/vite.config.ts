import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

import { API } from './src/lib/routes';

// Dev server binds all interfaces on a fixed port (:8765) so the laptop can reach buildhost's Vite.
// The API prefix is proxied to the FastAPI backend on :8001 — the data
// linkage. The typed client in src/lib/api fetches relative API paths
// (mirroring sol-next's vite proxy), so no CORS rules or hardcoded host
// leak into the app. The prefix itself comes from routes.ts (CENTRAL-006).
// allowedHosts: Vite 6 rejects non-IP Host headers it does not know
// (DNS-rebinding protection), which 403'd http://titan:8765 from the laptop.
// 'titan' is the one documented hostname entry point; IP hosts
// (10.0.12.10, 127.0.0.1) pass the check by default, so they are not listed.
// SOL_API_TARGET points a secondary dev instance (a session worktree running
// its own uvicorn on a free port) at its own backend; unset, the proxy goes
// to the canonical :8001.
const API_TARGET = process.env.SOL_API_TARGET ?? 'http://localhost:8001';

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 8765,
    allowedHosts: ['titan'],
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
