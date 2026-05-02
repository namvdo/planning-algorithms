import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  use: {
    baseURL: "http://127.0.0.1:5175",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: "python3 -m uvicorn app.main:app --host 127.0.0.1 --port 18080",
      cwd: "../backend",
      url: "http://127.0.0.1:18080/api/health",
      reuseExistingServer: false,
    },
    {
      command: "env VITE_API_URL=http://127.0.0.1:18080 npm run dev -- --port 5175",
      url: "http://127.0.0.1:5175",
      reuseExistingServer: false,
    },
  ],
});
