import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../drift_engine/api/static/dashboard",
    emptyOutDir: true,
    sourcemap: true
  },
  server: {
    proxy: {
      "/audit": "http://127.0.0.1:8080",
      "/baselines": "http://127.0.0.1:8080",
      "/collectors": "http://127.0.0.1:8080",
      "/drifts": "http://127.0.0.1:8080",
      "/health": "http://127.0.0.1:8080",
      "/integrations": "http://127.0.0.1:8080",
      "/jobs": "http://127.0.0.1:8080",
      "/remediation": "http://127.0.0.1:8080"
    }
  }
});
