/**
 * Test helper utilities
 */

import { Page, expect } from "@playwright/test";

/**
 * Wait for navigation to complete
 */
export async function waitForNavigation(page: Page, url?: string) {
  if (url) {
    await page.waitForURL(url);
  } else {
    await page.waitForLoadState("networkidle");
  }
}

/**
 * Wait for API response
 */
export async function waitForAPIResponse(
  page: Page,
  urlPattern: string | RegExp,
) {
  return page.waitForResponse((response) => {
    const url = response.url();
    if (typeof urlPattern === "string") {
      return url.includes(urlPattern);
    }
    return urlPattern.test(url);
  });
}

/**
 * Take a screenshot with automatic naming
 */
export async function takeScreenshot(page: Page, name: string) {
  await page.screenshot({
    path: `screenshots/${name}-${Date.now()}.png`,
    fullPage: true,
  });
}

/**
 * Check if element is visible
 */
export async function isVisible(
  page: Page,
  selector: string,
): Promise<boolean> {
  try {
    const element = page.locator(selector);
    return await element.isVisible({ timeout: 5000 });
  } catch {
    return false;
  }
}

/**
 * Wait for text to appear
 */
export async function waitForText(page: Page, text: string, timeout = 10000) {
  await page.waitForSelector(`text=${text}`, { timeout });
}

/**
 * Fill form field by label
 */
export async function fillByLabel(page: Page, label: string, value: string) {
  const input = page.locator(
    `label:has-text("${label}") + input, label:has-text("${label}") input`,
  );
  await input.fill(value);
}

/**
 * Click button by text
 */
export async function clickButton(page: Page, text: string) {
  await page.click(`button:has-text("${text}")`);
}

/**
 * Assert toast/notification appears
 */
export async function expectToast(page: Page, message: string) {
  const toast = page.locator(
    `[role="alert"]:has-text("${message}"), .toast:has-text("${message}")`,
  );
  await expect(toast).toBeVisible({ timeout: 5000 });
}

/**
 * Assert loading state completes
 */
export async function waitForLoadingComplete(page: Page) {
  // Wait for any loading spinners or skeletons to disappear
  await page
    .waitForSelector('.loading, [data-loading="true"], .skeleton', {
      state: "hidden",
      timeout: 10000,
    })
    .catch(() => {
      // If no loading indicator found, that's fine
    });
}

/**
 * Get text content of element
 */
export async function getTextContent(
  page: Page,
  selector: string,
): Promise<string> {
  const element = page.locator(selector);
  return (await element.textContent()) || "";
}

/**
 * Assert URL contains path
 */
export async function expectURLContains(page: Page, path: string) {
  await expect(page).toHaveURL(new RegExp(path));
}

/**
 * Retry action until it succeeds
 */
export async function retryUntilSuccess<T>(
  action: () => Promise<T>,
  maxAttempts = 3,
  delayMs = 1000,
): Promise<T> {
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await action();
    } catch (error) {
      if (attempt === maxAttempts) {
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
  }
  throw new Error("Should not reach here");
}

/**
 * Debug: Log current page state
 */
export async function debugPageState(page: Page) {
  console.log("Current URL:", page.url());
  console.log("Title:", await page.title());
  const cookies = await page.context().cookies();
  console.log("Cookies:", cookies.length);
  const localStorage = await page.evaluate(() => Object.keys(localStorage));
  console.log("LocalStorage keys:", localStorage);
}
