import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev server binds all interfaces so the laptop can reach buildhost's Vite.
export default defineConfig({
  plugins: [react()],
  server: { host: true },
});
