"""
E2E Test: Alex's Balanced Lifestyle Scenario

User: Alex Sterling
Persona: Balanced (Strictness 5/10)
Pattern: Healthy financial habits with reasonable splurges
"""

import pytest
from playwright.sync_api import Page, expect
from utils.auth import setup_authenticated_session
from utils.test_helpers import (
    wait_for_loading_complete,
    click_button,
    expect_url_contains,
)

ALEX_EMAIL = "demo+alex@fiscalguard.app"
ALEX_PASSWORD = "demo123"


@pytest.fixture
def alex_page(page: Page, base_url: str):
    """Authenticated page for Alex"""
    setup_authenticated_session(page, ALEX_EMAIL, ALEX_PASSWORD)
    page.goto(base_url)
    wait_for_loading_complete(page)
    return page


class TestAlexBalancedLifestyle:
    """Test suite for Alex's balanced lifestyle scenario"""

    def test_should_show_healthy_budget_status(self, alex_page: Page):
        """Verify healthy budget status is displayed"""
        alex_page.click('[href="/"]')
        wait_for_loading_complete(alex_page)

        # Should have good Guard Score
        guard_score = alex_page.locator('text=Guard Score')
        expect(guard_score).to_be_visible()

        # Most categories should be healthy
        healthy = alex_page.locator('text=Healthy')
        healthy_count = healthy.count()
        assert healthy_count > 0

    def test_should_get_balanced_recommendation_from_agent(self, alex_page: Page):
        """Verify balanced recommendations from agent"""
        alex_page.click('text=Shield')
        wait_for_loading_complete(alex_page)

        input_field = alex_page.locator('input, textarea').last
        input_field.fill('Should I buy concert tickets for $150?')
        click_button(alex_page, 'Send')

        # Wait for agent response
        alex_page.wait_for_timeout(5000)

        # Agent should provide balanced analysis
        response = alex_page.locator('[class*="agent"], [class*="assistant"]').last
        expect(response).to_be_visible(timeout=30000)

    def test_should_show_vacation_fund_progress(self, alex_page: Page):
        """Verify Vacation Fund progress is displayed"""
        alex_page.click('text=Vault')
        click_button(alex_page, 'Goals')
        wait_for_loading_complete(alex_page)

        vacation_fund = alex_page.locator('text=Vacation Fund')
        expect(vacation_fund).to_be_visible()

        # Should show 70% progress (3500/5000)
        progress = alex_page.locator('text=/3,?500|3500/')
        expect(progress).to_be_visible()

    def test_should_allow_contributing_to_vacation_fund(self, alex_page: Page):
        """Verify ability to contribute to Vacation Fund"""
        alex_page.click('text=Vault')
        click_button(alex_page, 'Goals')
        wait_for_loading_complete(alex_page)

        add_button = alex_page.locator('button:has-text("Add $")').first
        add_button.click()

        modal = alex_page.locator('text=Add Progress')
        expect(modal).to_be_visible()

        amount_input = alex_page.locator('input[type="number"]')
        amount_input.fill('500')

        click_button(alex_page, 'Add Progress')
        alex_page.wait_for_timeout(2000)

        # Should be 4000 now
        updated_amount = alex_page.locator('text=/4,?000|4000/')
        expect(updated_amount).to_be_visible(timeout=5000)

    def test_should_show_positive_feedback_on_past_concert_purchase(self, alex_page: Page):
        """Verify positive feedback on past concert ticket purchase"""
        alex_page.click('text=Insights')
        wait_for_loading_complete(alex_page)

        # Should see Concert Tickets decision
        concert = alex_page.locator('text=Concert Tickets')
        expect(concert).to_be_visible()

        # Should see positive satisfaction (low regret)
        satisfaction = concert.locator('..').locator('..').locator('text=Satisfaction')
        expect(satisfaction).to_be_visible()
