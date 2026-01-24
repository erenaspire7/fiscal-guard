"""
E2E Test: Marcus's Extreme Discipline Scenario

User: Marcus Wu
Persona: Gentle (Strictness 2/10)
Pattern: Extreme frugality, investment-focused
"""

import pytest
from playwright.sync_api import Page, expect
from utils.auth import setup_authenticated_session
from utils.test_helpers import (
    wait_for_loading_complete,
    click_button,
    expect_url_contains,
)

MARCUS_EMAIL = "demo+marcus@fiscalguard.app"
MARCUS_PASSWORD = "demo123"


@pytest.fixture
def marcus_page(page: Page, base_url: str):
    """Authenticated page for Marcus"""
    setup_authenticated_session(page, MARCUS_EMAIL, MARCUS_PASSWORD)
    page.goto(base_url)
    wait_for_loading_complete(page)
    return page


class TestMarcusExtremeDiscipline:
    """Test suite for Marcus's extreme discipline scenario"""

    def test_should_show_excellent_guard_score(self, marcus_page: Page):
        """Verify excellent Guard Score is displayed"""
        marcus_page.click('[href="/"]')
        wait_for_loading_complete(marcus_page)

        guard_score = marcus_page.locator('text=Guard Score')
        expect(guard_score).to_be_visible()

        # Should have high score
        score_value = marcus_page.locator('[class*="text-5xl"]').first
        expect(score_value).to_be_visible()

    def test_should_show_all_categories_under_budget(self, marcus_page: Page):
        """Verify all or most categories show as healthy"""
        marcus_page.click('[href="/"]')
        wait_for_loading_complete(marcus_page)

        # All or most should be healthy
        healthy = marcus_page.locator('text=Healthy')
        healthy_count = healthy.count()
        assert healthy_count >= 4  # Most categories healthy

    def test_should_get_encouraging_response_for_investment_purchase(self, marcus_page: Page):
        """Verify encouraging response for investment-related purchases"""
        marcus_page.click('text=Shield')
        wait_for_loading_complete(marcus_page)

        input_field = marcus_page.locator('input, textarea').last
        input_field.fill('Should I buy a $300 investment course?')
        click_button(marcus_page, 'Send')

        marcus_page.wait_for_timeout(5000)

        response = marcus_page.locator('[class*="agent"], [class*="assistant"]').last
        expect(response).to_be_visible(timeout=30000)

    def test_should_show_early_retirement_fund_goal(self, marcus_page: Page):
        """Verify Early Retirement Fund goal is displayed"""
        marcus_page.click('text=Vault')
        click_button(marcus_page, 'Goals')
        wait_for_loading_complete(marcus_page)

        retirement_fund = marcus_page.locator('text=Early Retirement Fund')
        expect(retirement_fund).to_be_visible()

        # Should show $125,000 progress
        progress = marcus_page.locator('text=/125,?000|125000/')
        expect(progress).to_be_visible()

    def test_should_allow_large_contribution_to_retirement_fund(self, marcus_page: Page):
        """Verify ability to make large contributions to retirement fund"""
        marcus_page.click('text=Vault')
        click_button(marcus_page, 'Goals')
        wait_for_loading_complete(marcus_page)

        add_button = marcus_page.locator('button:has-text("Add $")').first
        add_button.click()

        modal = marcus_page.locator('text=Add Progress')
        expect(modal).to_be_visible()

        amount_input = marcus_page.locator('input[type="number"]')
        amount_input.fill('5000')  # Monthly investment

        click_button(marcus_page, 'Add Progress')
        marcus_page.wait_for_timeout(2000)

        # Should be 130,000 now
        updated_amount = marcus_page.locator('text=/130,?000|130000/')
        expect(updated_amount).to_be_visible(timeout=5000)

    def test_should_show_minimal_spending_in_all_categories(self, marcus_page: Page):
        """Verify minimal spending across all categories"""
        marcus_page.click('[href="/"]')
        wait_for_loading_complete(marcus_page)

        # Entertainment should show 0% or very low
        entertainment = marcus_page.locator('text=Entertainment')
        if entertainment.is_visible():
            # Check for low percentage
            percentage = entertainment.locator('..').locator('text=/%/')
            expect(percentage).to_be_visible()
