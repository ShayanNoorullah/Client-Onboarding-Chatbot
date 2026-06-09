import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/ws": {
        target: "http://127.0.0.1:8001",
        ws: true,
        changeOrigin: true,
      },
      "/upload": { target: "http://127.0.0.1:8001", changeOrigin: true },
      "/client": { target: "http://127.0.0.1:8001", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8001", changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
});
