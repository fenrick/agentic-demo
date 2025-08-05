import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// Vite configuration for the React frontend. The project lives in the
// `frontend` directory, and built assets are emitted to `frontend/dist`.
export default defineConfig({
  root: "frontend",
  plugins: [react()],
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
