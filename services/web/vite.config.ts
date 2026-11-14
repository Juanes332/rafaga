/// <reference types="vitest/config" />
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Dev-only stand-in for the container entrypoint (ADR-05): serves /config.json from env.
function devRuntimeConfig(): Plugin {
  return {
    name: "rafaga-dev-runtime-config",
    apply: "serve",
    configureServer(server) {
      server.middlewares.use("/config.json", (_req, res) => {
        const apiPort = Number(process.env.RAFAGA_API_PORT ?? 8000);
        res.setHeader("Content-Type", "application/json");
        res.setHeader("Cache-Control", "no-store");
        res.end(JSON.stringify({ apiPort, apiBaseUrl: process.env.RAFAGA_API_BASE_URL ?? null }));
      });
    },
  };
}

export default defineConfig(({ mode }) => ({
  plugins: [react(), mode === "mock" ? null : devRuntimeConfig()],
  // Mock mode serves the MSW worker script; production builds never ship it.
  publicDir: mode === "mock" ? "tests/msw/public" : "public",
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  build: {
    chunkSizeWarningLimit: 1500,
  },
  test: {
    globals: false,
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/**/*.test.{ts,tsx}"],
    css: { modules: { classNameStrategy: "non-scoped" } },
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/components/ui/**", "src/main.tsx", "src/types/api/openapi.gen.ts"],
    },
  },
}));
