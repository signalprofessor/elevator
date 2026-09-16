import tailwindcss from "@tailwindcss/postcss";
import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";

export default defineConfig({
  root: "loopia",
  publicDir: "../public",
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./", import.meta.url)),
    },
  },
  plugins: [react()],
  css: { postcss: { plugins: [tailwindcss()] } },
  build: {
    outDir: "../loopia-dist",
    emptyOutDir: true,
    sourcemap: false,
  },
});
