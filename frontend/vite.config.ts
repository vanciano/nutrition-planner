import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Builds into the backend's static/ dir so FastAPI serves the SPA at /.
export default defineConfig({
  plugins: [react()],
  base: "/",
  build: {
    outDir: "../src/app/static",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
