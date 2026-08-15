import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev, the Vite server proxies /api and /ws to the backend directly
// (started separately on :8000). In production, nginx does this instead —
// see frontend/nginx.conf — so the app never hardcodes a backend origin.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // More specific rule first — Vite matches proxy keys in insertion order.
      "/api/ws/live": { target: "ws://localhost:8000", ws: true },
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});
