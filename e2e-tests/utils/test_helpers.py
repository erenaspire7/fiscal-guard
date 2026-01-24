"""
Test helper utilities
"""

import re
from typing import Optional
from playwright.sync_api import Page, expect


def wait_for_navigation(page: Page, url: Optional[str] = None) -> None:
    """Wait for navigation to complete"""
    if url:
        page.wait_for_url(url)
    else:
        page.wait_for_load_state("networkidle")


def wait_for_api_response(page: Page, url_pattern: str | re.Pattern):
    """Wait for API response"""
    def check_url(response):
        url = response.url
        if isinstance(url_pattern, str):
            return url_pattern in url
        return url_pattern.search(url) is not None

    return page.wait_for_response(check_url)


def is_visible(page: Page, selector: str) -> bool:
    """Check if element is visible"""
    try:
        element = page.locator(selector)
        return element.is_visible(timeout=5000)
    except Exception:
        return False


def wait_for_text(page: Page, text: str, timeout: int = 10000) -> None:
    """Wait for text to appear"""
    page.wait_for_selector(f"text={text}", timeout=timeout)


def fill_by_label(page: Page, label: str, value: str) -> None:
    """Fill form field by label"""
    input_selector = f'label:has-text("{label}") + input, label:has-text("{label}") input'
    page.locator(input_selector).fill(value)


def click_button(page: Page, text: str) -> None:
    """Click button by text"""
    page.click(f'button:has-text("{text}")')


def expect_toast(page: Page, message: str) -> None:
    """Assert toast/notification appears"""
    toast = page.locator(
        f'[role="alert"]:has-text("{message}"), .toast:has-text("{message}")'
    )
    expect(toast).to_be_visible(timeout=5000)


def wait_for_loading_complete(page: Page) -> None:
    """Assert loading state completes"""
    try:
        page.wait_for_selector(
            '.loading, [data-loading="true"], .skeleton',
            state="hidden",
            timeout=10000,
        )
    except Exception:
        # If no loading indicator found, that's fine
        pass


def get_text_content(page: Page, selector: str) -> str:
    """Get text content of element"""
    element = page.locator(selector)
    return element.text_content() or ""


def expect_url_contains(page: Page, path: str) -> None:
    """Assert URL contains path"""
    expect(page).to_have_url(re.compile(path))


def retry_until_success(action, max_attempts: int = 3, delay_ms: int = 1000):
    """Retry action until it succeeds"""
    import time

    for attempt in range(1, max_attempts + 1):
        try:
            return action()
        except Exception as e:
            if attempt == max_attempts:
                raise e
            time.sleep(delay_ms / 1000)


def debug_page_state(page: Page) -> None:
    """Debug: Log current page state"""
    print("Current URL:", page.url)
    print("Title:", page.title())
    cookies = page.context.cookies()
    print("Cookies:", len(cookies))
    local_storage = page.evaluate("() => Object.keys(localStorage)")
    print("LocalStorage keys:", local_storage)
