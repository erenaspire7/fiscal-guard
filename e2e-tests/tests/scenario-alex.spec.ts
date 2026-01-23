/**
 * E2E Test: Alex's Balanced Lifestyle Scenario
 *
 * User: Alex Sterling
 * Persona: Balanced (Strictness 5/10)
 * Pattern: Healthy financial habits with reasonable splurges
 */

import { test, expect } from '@playwright/test';
import { setupAuthenticatedSession } from '../utils/auth';
import {
  waitForLoadingComplete,
  clickButton,
  expectURLContains
} from '../utils/test-helpers';

const ALEX_EMAIL = 'demo+alex@fiscalguard.app';
const ALEX_PASSWORD = 'demo123';

test.describe('Scenario: Alex\'s Balanced Lifestyle', () => {
  test.beforeEach(async ({ page }) => {
    await setupAuthenticatedSession(page, ALEX_EMAIL, ALEX_PASSWORD);
    await page.goto('/');
    await waitForLoadingComplete(page);
  });

  test('should show healthy budget status', async ({ page }) => {
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    // Should have good Guard Score
    const guardScore = page.locator('text=Guard Score');
    await expect(guardScore).toBeVisible();

    // Most categories should be healthy
    const healthy = page.locator('text=Healthy');
    const healthyCount = await healthy.count();
    expect(healthyCount).toBeGreaterThan(0);
  });

  test('should get balanced recommendation from agent', async ({ page }) => {
    await page.click('text=Shield');
    await waitForLoadingComplete(page);

    const input = page.locator('input, textarea').last();
    await input.fill('Should I buy concert tickets for $150?');
    await clickButton(page, 'Send');

    // Wait for agent response
    await page.waitForTimeout(5000);

    // Agent should provide balanced analysis
    const response = page.locator('[class*="agent"], [class*="assistant"]').last();
    await expect(response).toBeVisible({ timeout: 30000 });
  });

  test('should show Vacation Fund progress', async ({ page }) => {
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    const vacationFund = page.locator('text=Vacation Fund');
    await expect(vacationFund).toBeVisible();

    // Should show 70% progress (3500/5000)
    const progress = page.locator('text=/3,?500|3500/');
    await expect(progress).toBeVisible();
  });

  test('should allow contributing to Vacation Fund', async ({ page }) => {
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    const addButton = page.locator('button:has-text("Add $")').first();
    await addButton.click();

    const modal = page.locator('text=Add Progress');
    await expect(modal).toBeVisible();

    const amountInput = page.locator('input[type="number"]');
    await amountInput.fill('500');

    await clickButton(page, 'Add Progress');
    await page.waitForTimeout(2000);

    // Should be 4000 now
    const updatedAmount = page.locator('text=/4,?000|4000/');
    await expect(updatedAmount).toBeVisible({ timeout: 5000 });
  });

  test('should show positive feedback on past concert purchase', async ({ page }) => {
    await page.click('text=Insights');
    await waitForLoadingComplete(page);

    // Should see Concert Tickets decision
    const concert = page.locator('text=Concert Tickets');
    await expect(concert).toBeVisible();

    // Should see positive satisfaction (low regret)
    const satisfaction = concert.locator('..').locator('..').locator('text=Satisfaction');
    await expect(satisfaction).toBeVisible();
  });
});
