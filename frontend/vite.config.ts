import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // 8080: avoids WinError 10013 on some PCs where 8000 is reserved/blocked
      "/api": { target: "http://127.0.0.1:8080", changeOrigin: true },
    },
  },
});
