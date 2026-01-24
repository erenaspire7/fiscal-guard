"""
Pytest configuration and fixtures for E2E tests
"""

import pytest
from playwright.sync_api import Page, Browser, BrowserContext
from utils.seed_data import seed_demo_data


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "record_video_dir": "videos/",
        "record_video_size": {"width": 1920, "height": 1080},
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_data():
    """Seed demo data before running any tests"""
    print("\n🌱 Setting up test data...\n")
    seed_demo_data()
    print("✅ Test data ready\n")
    yield
    print("\n✨ Tests completed\n")


@pytest.fixture
def base_url():
    """Base URL for the application"""
    import os
    return os.getenv("APP_URL", "http://localhost:5173")


@pytest.fixture
def app_page(page: Page, base_url: str):
    """Page fixture that navigates to the app"""
    page.goto(base_url)
    return page
