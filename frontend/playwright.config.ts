import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 90000,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'off',
  },
  outputDir: '../artifacts/test-results',
  reporter: [['list']],
});
