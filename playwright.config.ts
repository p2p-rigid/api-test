import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  use: {
    headless: false,
    viewport: { width: 1280, height: 720 },
  },
});
