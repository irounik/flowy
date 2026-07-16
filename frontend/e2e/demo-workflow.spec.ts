/**
 * Records a demo video: create a dynamic workflow and execute it.
 */
import { test, expect } from '@playwright/test';

test.use({
  video: 'on',
  viewport: { width: 1440, height: 900 },
  launchOptions: { slowMo: 250 },
});

test('create and execute dynamic workflow', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.waitForSelector('[data-testid="workflow-name"]');

  // Name the workflow
  await page.getByTestId('workflow-name').fill('Demo Research Flow');
  await page.waitForTimeout(400);

  // Start blank canvas
  await page.getByRole('button', { name: 'Blank workflow' }).click();
  await page.waitForTimeout(500);

  // Add nodes from palette (click to add) — order matters for execution
  for (const type of ['trigger', 'tool', 'llm', 'notification']) {
    await page.getByTestId(`palette-${type}`).click();
    await page.waitForTimeout(500);
  }

  // Connect nodes sequentially
  const rightHandles = page.locator('.react-flow__handle-right');
  const leftHandles = page.locator('.react-flow__handle-left');
  for (let i = 0; i < 3; i++) {
    const source = rightHandles.nth(i);
    const target = leftHandles.nth(i);
    const srcBox = await source.boundingBox();
    const tgtBox = await target.boundingBox();
    if (srcBox && tgtBox) {
      await page.mouse.move(srcBox.x + srcBox.width / 2, srcBox.y + srcBox.height / 2);
      await page.mouse.down();
      await page.mouse.move(tgtBox.x + tgtBox.width / 2, tgtBox.y + tgtBox.height / 2, { steps: 15 });
      await page.mouse.up();
      await page.waitForTimeout(400);
    }
  }

  // Configure LLM node prompt
  await page.locator('.react-flow__node').nth(2).click();
  await page.waitForTimeout(400);
  const prompt = page.getByLabel('Prompt template');
  if (await prompt.isVisible()) {
    await prompt.fill('Summarize research findings into an executive brief.');
    await page.waitForTimeout(300);
  }

  // Run workflow
  await page.getByTestId('run-workflow').click();
  await expect(page.getByText(/Execution started/i)).toBeVisible({ timeout: 15000 });
  await page.waitForTimeout(1000);

  // View executions
  await page.getByTestId('nav-executions').click();
  await page.waitForTimeout(800);

  // Wait for completion (mock LLM ~3s total)
  await expect(page.getByText('COMPLETED').first()).toBeVisible({ timeout: 20000 });
  await page.waitForTimeout(1500);
});
