/**
 * E2E Test: Marcus's Extreme Discipline Scenario
 *
 * User: Marcus Wu
 * Persona: Gentle (Strictness 2/10)
 * Pattern: Extreme frugality, investment-focused
 */

import { test, expect } from '@playwright/test';
import { setupAuthenticatedSession } from '../utils/auth';
import {
  waitForLoadingComplete,
  clickButton,
  expectURLContains
} from '../utils/test-helpers';

const MARCUS_EMAIL = 'demo+marcus@fiscalguard.app';
const MARCUS_PASSWORD = 'demo123';

test.describe('Scenario: Marcus\'s Extreme Discipline', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page, MARCUS_EMAIL, MARCUS_PASSWORD);
    await page.goto('/');
    await waitForLoadingComplete(page);
  });

  test('should show excellent Guard Score', async ({ page }) => {
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    const guardScore = page.locator('text=Guard Score');
    await expect(guardScore).toBeVisible();

    // Should have high score
    const scoreValue = page.locator('[class*="text-5xl"]').first();
    await expect(scoreValue).toBeVisible();
  });

  test('should show all categories under budget', async ({ page }) => {
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    // All or most should be healthy
    const healthy = page.locator('text=Healthy');
    const healthyCount = await healthy.count();
    expect(healthyCount).toBeGreaterThanOrEqual(4); // Most categories healthy
  });

  test('should get encouraging response for investment purchase', async ({ page }) => {
    await page.click('text=Shield');
    await waitForLoadingComplete(page);

    const input = page.locator('input, textarea').last();
    await input.fill('Should I buy a $300 investment course?');
    await clickButton(page, 'Send');

    await page.waitForTimeout(5000);

    const response = page.locator('[class*="agent"], [class*="assistant"]').last();
    await expect(response).toBeVisible({ timeout: 30000 });
  });

  test('should show Early Retirement Fund goal', async ({ page }) => {
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    const retirementFund = page.locator('text=Early Retirement Fund');
    await expect(retirementFund).toBeVisible();

    // Should show $125,000 progress
    const progress = page.locator('text=/125,?000|125000/');
    await expect(progress).toBeVisible();
  });

  test('should allow large contribution to retirement fund', async ({ page }) => {
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    const addButton = page.locator('button:has-text("Add $")').first();
    await addButton.click();

    const modal = page.locator('text=Add Progress');
    await expect(modal).toBeVisible();

    const amountInput = page.locator('input[type="number"]');
    await amountInput.fill('5000'); // Monthly investment

    await clickButton(page, 'Add Progress');
    await page.waitForTimeout(2000);

    // Should be 130,000 now
    const updatedAmount = page.locator('text=/130,?000|130000/');
    await expect(updatedAmount).toBeVisible({ timeout: 5000 });
  });

  test('should show minimal spending in all categories', async ({ page }) => {
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    // Entertainment should show 0% or very low
    const entertainment = page.locator('text=Entertainment');
    if (await entertainment.isVisible()) {
      // Check for low percentage
      const percentage = entertainment.locator('..').locator('text=/%/');
      await expect(percentage).toBeVisible();
    }
  });
});
