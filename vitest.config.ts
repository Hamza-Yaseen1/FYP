import { defineConfig } from "vitest/config";
import path from "path";

export default defineConfig({
  test: {
    environment: "node",
    include: ["app/**/*.test.ts", "tests/**/*.test.ts"],
    exclude: ["node_modules", ".next", "backend", ".opencode"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname),
    },
  },
});
