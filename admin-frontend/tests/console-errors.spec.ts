import { test, expect, Page } from '@playwright/test';

async function navigateToTracker(page: Page) {
  const selectors = [
    'a[data-value="reporting_effort_tracker"]',
    'a[href="#shiny-tab-reporting_effort_tracker"]',
    'a[data-toggle="tab"][data-value="reporting_effort_tracker"]',
    '.nav-link[data-value="reporting_effort_tracker"]'
  ];

  for (const sel of selectors) {
    try {
      await page.waitForSelector(sel, { timeout: 5000 });
      await page.click(sel);
      return;
    } catch (e) {
      // try next selector
    }
  }
  throw new Error('Could not find Reporting Effort Tracker tab');
}

test('Console error check on tracker load', async ({ page }) => {
  const consoleErrors: string[] = [];
  const consoleWarnings: string[] = [];

  page.on('console', msg => {
    const entry = `[${msg.type()}] ${msg.text()}`;
    if (msg.type() === 'error') {
      consoleErrors.push(entry);
    } else if (msg.type() === 'warning') {
      consoleWarnings.push(entry);
    }
    // Always print to runner output for debugging
    console.log(entry);
  });

  // Open app
  await page.goto('/', { waitUntil: 'load' });

  // Go to tracker tab
  await navigateToTracker(page);

  // Wait for at least one comment button to appear
  await page.waitForSelector('.comment-btn[data-tracker-id]', { timeout: 30000 });

  // Give client-side handlers time to hydrate badges
  await page.waitForTimeout(1500);

  // Sample up to 5 buttons and log their counts
  const counts = await page.$$eval('.comment-btn[data-tracker-id]', buttons =>
    (buttons as HTMLElement[]).slice(0, 5).map(btn => ({
      id: btn.getAttribute('data-tracker-id'),
      count: btn.getAttribute('data-unresolved-count'),
      classes: btn.className
    }))
  );
  console.log('Badge samples:', JSON.stringify(counts, null, 2));

  // Fail if there are any console errors
  expect(consoleErrors, `Console errors found:\n${consoleErrors.join('\n')}`).toHaveLength(0);

  // Soft assert on warnings (surface but don't fail)
  if (consoleWarnings.length) {
    console.log('Console warnings observed:\n' + consoleWarnings.join('\n'));
  }
});


