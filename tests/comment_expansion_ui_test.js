// Playwright test for comment expansion UI
// Tests expandable rows, comment forms, and real-time updates

const { test, expect } = require('@playwright/test');

test.describe('Comment System - Expandable Rows', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the reporting effort tracker
    await page.goto('http://localhost:3838');
    
    // Wait for the page to load
    await page.waitForSelector('.navbar');
    
    // Navigate to Reporting Effort Tracker
    await page.click('text=Tracker Management');
    await page.waitForSelector('[data-testid="tracker-table"]', { timeout: 10000 });
  });

  test('should display comment buttons in tracker tables', async ({ page }) => {
    // Check if comment buttons are present
    const commentButtons = await page.locator('.comment-expand-btn');
    await expect(commentButtons.first()).toBeVisible();
    
    // Verify button has proper text/icon
    await expect(commentButtons.first()).toContainText(['No Comments', 'Comments', 'New', 'Resolved']);
  });

  test('should expand row when comment button is clicked', async ({ page }) => {
    // Click the first comment button
    const firstCommentButton = page.locator('.comment-expand-btn').first();
    await firstCommentButton.click();
    
    // Check if expansion container appears
    await expect(page.locator('.comment-expansion-container')).toBeVisible();
    
    // Verify comment container structure
    await expect(page.locator('.card-header')).toContainText('Comments for Tracker ID:');
    await expect(page.locator('.comment-form')).toBeVisible();
    await expect(page.locator('.comments-list')).toBeVisible();
  });

  test('should show add comment form when Add Comment button is clicked', async ({ page }) => {
    // Expand a row first
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Click Add Comment button
    await page.click('text=Add Comment');
    
    // Verify form elements are visible
    await expect(page.locator('#comment-type-1')).toBeVisible();
    await expect(page.locator('#comment-text-1')).toBeVisible();
    await expect(page.locator('#track-comment-1')).toBeVisible();
    
    // Verify submit and cancel buttons
    await expect(page.locator('text=Add Comment').nth(1)).toBeVisible(); // Submit button
    await expect(page.locator('text=Cancel')).toBeVisible();
  });

  test('should validate comment form submission', async ({ page }) => {
    // Expand a row
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Open comment form
    await page.click('text=Add Comment');
    
    // Try to submit empty comment
    await page.click('text=Add Comment', { nth: 1 }); // Submit button
    
    // Should see validation message
    await expect(page.locator('text=Please enter a comment')).toBeVisible({ timeout: 5000 });
  });

  test('should successfully submit a comment', async ({ page }) => {
    // Expand a row
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Open comment form
    await page.click('text=Add Comment');
    
    // Fill in comment form
    await page.selectOption('#comment-type-1', 'qc_comment');
    await page.fill('#comment-text-1', 'This is a test comment for UI testing');
    await page.check('#track-comment-1');
    
    // Submit comment
    await page.click('text=Add Comment', { nth: 1 });
    
    // Wait for comment to appear
    await expect(page.locator('.comment-card')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('text=This is a test comment for UI testing')).toBeVisible();
  });

  test('should collapse row when comment button is clicked again', async ({ page }) => {
    // Expand a row
    const commentButton = page.locator('.comment-expand-btn').first();
    await commentButton.click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Click again to collapse
    await commentButton.click();
    
    // Verify expansion container is hidden
    await expect(page.locator('.comment-expansion-container')).not.toBeVisible();
  });

  test('should handle multiple expanded rows simultaneously', async ({ page }) => {
    const commentButtons = page.locator('.comment-expand-btn');
    const buttonCount = await commentButtons.count();
    
    if (buttonCount >= 2) {
      // Expand first row
      await commentButtons.nth(0).click();
      await page.waitForSelector('.comment-expansion-container');
      
      // Expand second row
      await commentButtons.nth(1).click();
      
      // Both should be visible
      const containers = page.locator('.comment-expansion-container');
      await expect(containers).toHaveCount(2);
    }
  });

  test('should display different comment types with proper styling', async ({ page }) => {
    // Expand a row
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Check comment type options
    await page.click('text=Add Comment');
    
    const typeSelect = page.locator('#comment-type-1');
    await expect(typeSelect).toBeVisible();
    
    // Verify all comment types are available
    const options = await typeSelect.locator('option').allTextContents();
    expect(options).toContain('QC Comment');
    expect(options).toContain('Production Comment');
    expect(options).toContain('Biostat Comment');
  });

  test('should show loading state while fetching comments', async ({ page }) => {
    // Expand a row
    await page.locator('.comment-expand-btn').first().click();
    
    // Should see loading message initially
    await expect(page.locator('text=Loading comments...')).toBeVisible();
  });

  test('should handle empty comment state gracefully', async ({ page }) => {
    // Expand a row that likely has no comments
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Should see empty state message
    await expect(page.locator('text=No comments yet')).toBeVisible({ timeout: 5000 });
  });

  test('should maintain table functionality with expanded rows', async ({ page }) => {
    // Expand a row
    await page.locator('.comment-expand-btn').first().click();
    await page.waitForSelector('.comment-expansion-container');
    
    // Try table operations like sorting, searching
    const searchBox = page.locator('input[type="search"]');
    if (await searchBox.isVisible()) {
      await searchBox.fill('test');
      await page.waitForTimeout(1000);
      
      // Table should still function
      await expect(page.locator('.comment-expansion-container')).toBeVisible();
    }
    
    // Try pagination if available
    const paginationNext = page.locator('.paginate_button.next');
    if (await paginationNext.isVisible() && !(await paginationNext.hasClass('disabled'))) {
      await paginationNext.click();
      await page.waitForTimeout(1000);
    }
  });
});

test.describe('Comment System - Real-time Updates', () => {
  test('should receive real-time comment updates', async ({ browser }) => {
    // Create two browser contexts to test real-time sync
    const context1 = await browser.newContext();
    const context2 = await browser.newContext();
    
    const page1 = await context1.newPage();
    const page2 = await context2.newPage();
    
    // Navigate both pages to tracker
    await page1.goto('http://localhost:3838');
    await page2.goto('http://localhost:3838');
    
    await page1.click('text=Tracker Management');
    await page2.click('text=Tracker Management');
    
    await page1.waitForSelector('.comment-expand-btn');
    await page2.waitForSelector('.comment-expand-btn');
    
    // Expand same row on both pages
    await page1.locator('.comment-expand-btn').first().click();
    await page2.locator('.comment-expand-btn').first().click();
    
    // Add comment on page1
    await page1.click('text=Add Comment');
    await page1.fill('#comment-text-1', 'Real-time test comment');
    await page1.click('text=Add Comment', { nth: 1 });
    
    // Check if comment appears on page2
    await expect(page2.locator('text=Real-time test comment')).toBeVisible({ timeout: 10000 });
    
    await context1.close();
    await context2.close();
  });
});

test.describe('Comment System - Accessibility', () => {
  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('http://localhost:3838');
    await page.click('text=Tracker Management');
    await page.waitForSelector('.comment-expand-btn');
    
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    const focusedElement = await page.evaluate(() => document.activeElement.className);
    
    // Continue tabbing to comment button
    let tabCount = 0;
    while (tabCount < 20 && !focusedElement.includes('comment-expand-btn')) {
      await page.keyboard.press('Tab');
      tabCount++;
    }
    
    // Press Enter to activate comment button
    await page.keyboard.press('Enter');
    
    // Should expand
    await expect(page.locator('.comment-expansion-container')).toBeVisible({ timeout: 5000 });
  });

  test('should have proper ARIA labels', async ({ page }) => {
    await page.goto('http://localhost:3838');
    await page.click('text=Tracker Management');
    await page.waitForSelector('.comment-expand-btn');
    
    // Check for ARIA attributes
    const commentButton = page.locator('.comment-expand-btn').first();
    const ariaLabel = await commentButton.getAttribute('aria-label');
    const title = await commentButton.getAttribute('title');
    
    // Should have descriptive text
    expect(ariaLabel || title).toBeTruthy();
  });
});

test.describe('Comment System - Mobile Responsiveness', () => {
  test('should work on mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('http://localhost:3838');
    await page.click('text=Tracker Management');
    await page.waitForSelector('.comment-expand-btn');
    
    // Click comment button
    await page.locator('.comment-expand-btn').first().click();
    
    // Should still expand properly on mobile
    await expect(page.locator('.comment-expansion-container')).toBeVisible();
    
    // Form should be usable
    await page.click('text=Add Comment');
    await expect(page.locator('#comment-text-1')).toBeVisible();
    
    // Touch targets should be adequate size
    const button = page.locator('text=Add Comment').nth(1);
    const boundingBox = await button.boundingBox();
    expect(boundingBox.height).toBeGreaterThan(40); // Minimum touch target
  });
});