import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  esbuild: {
    jsx: "automatic",
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      include: [
        "src/shared/roles.ts",
        "src/shared/permissions.ts",
        "src/shared/role-permissions.ts",
        "src/shared/navigation/**/*.ts",
        "src/shared/auth/PermissionGuard.tsx",
        "src/shared/auth/RoleGuard.tsx",
        "src/shared/mocks/portal.ts",
        "src/page-views/registry.ts",
        "src/layouts/Breadcrumb.tsx",
      ],
      thresholds: {
        lines: 90,
        functions: 90,
        branches: 90,
        statements: 90,
      },
    },
  },
  resolve: {
    alias: [
      { find: "@/pages", replacement: path.resolve(__dirname, "src/page-views") },
      { find: "@", replacement: path.resolve(__dirname, "src") },
    ],
  },
});
