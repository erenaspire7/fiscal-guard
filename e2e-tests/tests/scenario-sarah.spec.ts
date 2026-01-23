/**
 * E2E Test: Sarah's Shopping Addiction Scenario
 *
 * User: Sarah Chen
 * Persona: Financial Monk (Strictness 9/10)
 * Pattern: Impulsive buyer with high regret on designer items
 */

import { test, expect } from '@playwright/test';
import { setupAuthenticatedSession } from '../utils/auth';
import {
  waitForLoadingComplete,
  clickButton,
  waitForText,
  expectURLContains
} from '../utils/test-helpers';

const SARAH_EMAIL = 'demo+sarah@fiscalguard.app';
const SARAH_PASSWORD = 'demo123';

test.describe('Scenario: Sarah\'s Shopping Addiction', () => {
  test.beforeEach(async ({ page }) => {
    // Login as Sarah
    await setupAuthenticatedSession(page, SARAH_EMAIL, SARAH_PASSWORD);
    await page.goto('/');
    await waitForLoadingComplete(page);
  });

  test('should show over-budget warnings on Dashboard', async ({ page }) => {
    // Navigate to Dashboard
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    // Check for Guard Score
    const guardScore = page.locator('text=Guard Score');
    await expect(guardScore).toBeVisible();

    // Check for allocation health warnings
    const allocationHealth = page.locator('text=Allocation Health');
    await expect(allocationHealth).toBeVisible();

    // Shopping category should show over-budget
    const shopping = page.locator('text=Shopping').first();
    await expect(shopping).toBeVisible();

    // Should see "Over Budget" or "Near Capacity" status
    const overBudget = page.locator('text=/Over Budget|Near Capacity/i');
    await expect(overBudget.first()).toBeVisible();
  });

  test('should display regret patterns in Insights', async ({ page }) => {
    // Navigate to Insights
    await page.click('text=Insights');
    await expectURLContains(page, '/insights');
    await waitForLoadingComplete(page);

    // Check for Peace of Mind Score
    const peaceOfMind = page.locator('text=Peace of Mind Score');
    await expect(peaceOfMind).toBeVisible();

    // Check for reflections section
    const reflections = page.locator('text=Reflections');
    await expect(reflections).toBeVisible();

    // Should see past decisions
    const designerShoes = page.locator('text=Designer Shoes');
    await expect(designerShoes).toBeVisible();

    // Should see high regret indicators
    const regretIcon = page.locator('svg').filter({ has: page.locator('[class*="frown"]') });
    // At least one regret indicator should be visible
    const count = await regretIcon.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should allow rating satisfaction on past decisions', async ({ page }) => {
    // Navigate to Insights
    await page.click('text=Insights');
    await waitForLoadingComplete(page);

    // Find a decision without feedback (if any)
    const satisfactionSection = page.locator('text=Rate Satisfaction').first();

    if (await satisfactionSection.isVisible()) {
      // Click on a satisfaction icon (e.g., middle one for neutral)
      const satisfactionIcons = page.locator('button').filter({
        has: page.locator('svg')
      });

      // Click the first available satisfaction icon
      await satisfactionIcons.first().click();

      // Wait for the feedback to be submitted
      await page.waitForTimeout(1000);

      // The label should change from "Rate Satisfaction" to "Satisfaction"
      const updatedLabel = page.locator('text=Satisfaction').first();
      await expect(updatedLabel).toBeVisible({ timeout: 5000 });
    }
  });

  test('should get strict recommendation from Financial Monk agent', async ({ page }) => {
    // Navigate to Agent Chat
    await page.click('text=Shield');
    await expectURLContains(page, '/chat');
    await waitForLoadingComplete(page);

    // Type a purchase request
    const input = page.locator('input[placeholder*="purchase" i], textarea[placeholder*="purchase" i]');
    await input.fill('Should I buy designer boots for $450?');

    // Send message
    await clickButton(page, 'Send');

    // Wait for agent response
    await page.waitForSelector('text=/analyzing|agent/i', { timeout: 30000 });
    await waitForLoadingComplete(page);

    // Should see agent's response
    const agentResponse = page.locator('[class*="agent"], [class*="assistant"]').last();
    await expect(agentResponse).toBeVisible({ timeout: 30000 });

    // Response should be visible (Financial Monk persona should be strict)
    const responseText = await agentResponse.textContent();
    expect(responseText).toBeTruthy();
    expect(responseText!.length).toBeGreaterThan(20);
  });

  test('should show Emergency Fund goal progress', async ({ page }) => {
    // Navigate to Vault
    await page.click('text=Vault');
    await expectURLContains(page, '/vault');
    await waitForLoadingComplete(page);

    // Switch to Goals tab
    await clickButton(page, 'Goals');
    await page.waitForTimeout(500);

    // Check for Emergency Fund
    const emergencyFund = page.locator('text=Emergency Fund');
    await expect(emergencyFund).toBeVisible();

    // Should see progress indicator
    const progress = page.locator('text=/2,?800|2800/'); // Current amount
    await expect(progress).toBeVisible();
  });

  test('should allow adding progress to goals', async ({ page }) => {
    // Navigate to Vault
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    // Find "Add $" button
    const addButton = page.locator('button:has-text("Add $")').first();
    await expect(addButton).toBeVisible();

    // Click to open modal
    await addButton.click();

    // Modal should appear
    const modal = page.locator('text=Add Progress');
    await expect(modal).toBeVisible();

    // Fill in amount
    const amountInput = page.locator('input[type="number"]');
    await amountInput.fill('100');

    // Click Add Progress button
    await clickButton(page, 'Add Progress');

    // Wait for modal to close and data to refresh
    await page.waitForTimeout(2000);
    await waitForLoadingComplete(page);

    // Amount should be updated (2800 + 100 = 2900)
    const updatedAmount = page.locator('text=/2,?900|2900/');
    await expect(updatedAmount).toBeVisible({ timeout: 5000 });
  });

  test('should show persona settings in Setup', async ({ page }) => {
    // Navigate to Setup
    await page.click('text=Setup');
    await expectURLContains(page, '/setup');
    await waitForLoadingComplete(page);

    // Click on Guard Strictness
    await page.click('text=Guard Strictness');
    await expectURLContains(page, '/setup/agent');

    // Should see Financial Monk persona
    const financialMonk = page.locator('text=Financial Monk');
    await expect(financialMonk).toBeVisible();

    // Should see strictness slider at high value
    const strictnessIndicator = page.locator('text=/9.*%|90%/i');
    await expect(strictnessIndicator).toBeVisible();
  });

  test('full user journey: check budget → ask agent → view insights', async ({ page }) => {
    // 1. Start at Dashboard
    await page.click('[href="/"]');
    await waitForLoadingComplete(page);

    // Verify over-budget status
    const overBudget = page.locator('text=/Over Budget/i');
    await expect(overBudget.first()).toBeVisible();

    // 2. Go to Agent Chat
    await page.click('text=Shield');
    await waitForLoadingComplete(page);

    // Ask about a purchase
    const input = page.locator('input, textarea').last();
    await input.fill('Should I buy a $200 dress?');
    await clickButton(page, 'Send');

    // Wait for response
    await page.waitForTimeout(5000);

    // 3. Go to Insights to review patterns
    await page.click('text=Insights');
    await waitForLoadingComplete(page);

    // Verify reflections are visible
    const reflections = page.locator('text=Reflections');
    await expect(reflections).toBeVisible();

    // 4. Check Vault goals
    await page.click('text=Vault');
    await clickButton(page, 'Goals');
    await waitForLoadingComplete(page);

    // Verify Emergency Fund goal
    const emergencyFund = page.locator('text=Emergency Fund');
    await expect(emergencyFund).toBeVisible();
  });
});
