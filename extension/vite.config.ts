import fs from "fs";
import path from "path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
import webExtension from "vite-plugin-web-extension";

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    webExtension({
      manifest: () => {
        const manifest = JSON.parse(
          fs.readFileSync("src/manifest.json", "utf-8"),
        );
        // Inject Google Client ID from environment variable
        if (process.env.VITE_GOOGLE_CLIENT_ID) {
          manifest.oauth2.client_id = process.env.VITE_GOOGLE_CLIENT_ID;
        }
        return manifest;
      },
      watchFilePaths: ["src/manifest.json"],
    }),
  ],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  define: {
    // Polyfill process for browser environment (some dependencies check for it)
    "process.env.NODE_ENV": JSON.stringify(
      process.env.NODE_ENV || "production",
    ),
    "process.env": "{}",
    // Define global process object for libraries that access it directly
    global: "globalThis",
  },
  build: {
    outDir: "dist",
    // Let vite-plugin-web-extension handle all entry points from manifest.json
    // Do not specify manual rollupOptions.input as it conflicts with the plugin
  },
});
