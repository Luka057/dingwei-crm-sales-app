import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // 默认仍是 5173 / localhost:3000，不影响平时用法；
    // 需要避开端口冲突时，用环境变量临时改(VITE_DEV_PORT / VITE_PROXY_TARGET)
    port: Number(process.env.VITE_DEV_PORT) || 5173,
    host: "0.0.0.0",
    proxy: {
      "/api": process.env.VITE_PROXY_TARGET || "http://localhost:3000"
    }
  }
});
