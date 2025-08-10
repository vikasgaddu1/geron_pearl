import { test, expect } from '@playwright/test';

test.describe('Study Management Tree - Hierarchical CRUD', () => {
  test('add/edit/delete with scoped Add Child behavior', async ({ page }) => {
    // Navigate to app
    await page.goto('/');

    // Go to Data Management → Study Management
    await page.getByRole('button', { name: 'Data Management' }).click();
    await page.getByRole('link', { name: 'Study Management' }).click();

    // Add Study
    await page.getByRole('button', { name: 'Add Study' }).click();
    const uniq = `ST_${Date.now()}`;
    await page.getByPlaceholder('Enter unique study identifier').fill(uniq);
    await page.getByRole('button', { name: 'Create' }).click();

    // Verify study appears in tree
    await expect(page.getByText(uniq)).toBeVisible();

    // Add Child under study -> Database Release
    await page.getByText(uniq, { exact: true }).click();
    await page.getByRole('button', { name: 'Add Child' }).click();
    const rel = `REL_${Date.now()}`;
    await page.getByPlaceholder('Enter database release label').fill(rel);
    await page.getByRole('button', { name: 'Create' }).click();
    await expect(page.getByText(rel)).toBeVisible();

    // Add Child under release -> Reporting Effort
    await page.getByText(rel, { exact: true }).click();
    await page.getByRole('button', { name: 'Add Child' }).click();
    const eff = `EFF_${Date.now()}`;
    await page.getByPlaceholder('Enter reporting effort label').fill(eff);
    await page.getByRole('button', { name: 'Create' }).click();
    await expect(page.getByText(eff)).toBeVisible();

    // Verify Add Child is disabled for effort
    await page.getByText(eff, { exact: true }).click();
    const addChildBtn = page.getByRole('button', { name: 'Add Child' });
    await expect(addChildBtn).toBeDisabled();

    // Edit effort label
    await page.getByRole('button', { name: 'Edit' }).click();
    const effEdit = `${eff}_EDIT`;
    await page.getByPlaceholder('Enter reporting effort label').fill(effEdit);
    await page.getByRole('button', { name: 'Save' }).click();
    await expect(page.getByText(effEdit)).toBeVisible();

    // Delete effort, then release, then study
    await page.getByText(effEdit, { exact: true }).click();
    await page.getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText(effEdit)).toHaveCount(0);

    await page.getByText(rel, { exact: true }).click();
    await page.getByRole('button', { name: 'Delete' }).click();
    // Confirm delete
    await page.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText(rel)).toHaveCount(0);

    await page.getByText(uniq, { exact: true }).click();
    await page.getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Delete' }).click();
    await expect(page.getByText(uniq)).toHaveCount(0);
  });
});


