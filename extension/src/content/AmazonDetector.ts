/**
 * Amazon page detector - identifies cart/checkout pages
 */

export interface PageInfo {
  isAmazon: boolean;
  pageType: "cart" | "checkout" | "product" | "unknown";
  url: string;
}

export class AmazonDetector {
  /**
   * Detect if current page is Amazon and what type
   */
  detect(): PageInfo {
    const url = window.location.href;
    const hostname = window.location.hostname;

    // Check if Amazon domain
    const isAmazon =
      /amazon\.(com|co\.uk|de|fr|it|es|ca|com\.au|co\.jp|in|com\.br|com\.mx|nl|se|com\.tr|ae|sg)/.test(
        hostname,
      );

    if (!isAmazon) {
      return {
        isAmazon: false,
        pageType: "unknown",
        url,
      };
    }

    // Detect page type based on URL patterns
    let pageType: PageInfo["pageType"] = "unknown";

    if (/\/gp\/cart\/view\.html/.test(url) || /\/cart/.test(url)) {
      pageType = "cart";
    } else if (
      /\/gp\/buy\/spc\/handlers\/display\.html/.test(url) ||
      /\/checkout/.test(url) ||
      /\/gp\/buy/.test(url)
    ) {
      pageType = "checkout";
    } else if (/\/dp\//.test(url) || /\/gp\/product\//.test(url)) {
      pageType = "product";
    }

    return {
      isAmazon,
      pageType,
      url,
    };
  }

  /**
   * Check if cart area is visible on page
   */
  isCartAreaVisible(): boolean {
    // Look for common Amazon cart selectors
    const cartSelectors = [
      "#sc-active-cart",
      "#activeCartViewForm",
      ".sc-list-body",
      '[data-name="Active Items"]',
    ];

    for (const selector of cartSelectors) {
      const element = document.querySelector(selector);
      if (element && this.isElementVisible(element)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Get cart container element
   */
  getCartContainer(): HTMLElement | null {
    const selectors = [
      "#sc-active-cart",
      "#activeCartViewForm",
      ".sc-list-body",
      '[data-name="Active Items"]',
    ];

    for (const selector of selectors) {
      const element = document.querySelector(selector) as HTMLElement;
      if (element && this.isElementVisible(element)) {
        return element;
      }
    }

    return null;
  }

  /**
   * Check if element is visible in viewport
   */
  private isElementVisible(element: Element): boolean {
    const rect = element.getBoundingClientRect();
    // Check if element has size and overlaps with viewport
    return (
      rect.width > 0 &&
      rect.height > 0 &&
      rect.top < window.innerHeight &&
      rect.bottom > 0
    );
  }

  /**
   * Scroll cart into view if needed
   */
  async scrollCartIntoView(): Promise<void> {
    const cartContainer = this.getCartContainer();
    if (!cartContainer) {
      return;
    }

    cartContainer.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });

    // Wait for scroll to complete
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}
