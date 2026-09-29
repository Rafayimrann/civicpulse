/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Crucial config, per the brief: the frontend never bakes an absolute API
// URL into the build. In dev, Vite's proxy forwards /api to the backend
// container. In production, nginx does the same job (see nginx.conf) - so
// one built image runs unmodified in any environment; only the proxy
// target changes, and that lives outside the JS bundle entirely.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: process.env.VITE_DEV_PROXY_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./tests/setup.ts",
  },
});
