import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import tailwindcss from "@tailwindcss/vite";

// Vite configuration for the React frontend. The project lives in the
// `frontend` directory, and built assets are emitted to `frontend/dist`.
export default defineConfig({
  root: "frontend",
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/stream": {
        target: "http://localhost:8000",
        ws: false,
        changeOrigin: true,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "frontend/src"),
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
