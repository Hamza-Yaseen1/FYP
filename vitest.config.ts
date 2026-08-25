import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "jsdom",
    include: ["app/**/*.test.ts", "app/**/*.test.tsx", "components/**/*.test.tsx", "tests/**/*.test.ts"],
    exclude: ["node_modules", ".next", "backend", ".opencode"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname),
    },
  },
});
