"""
E2E Test: Sarah's Shopping Addiction Scenario

User: Sarah Chen
Persona: Financial Monk (Strictness 9/10)
Pattern: Impulsive buyer with high regret on designer items
"""

import pytest
from playwright.sync_api import Page, expect
from utils.auth import setup_authenticated_session
from utils.test_helpers import (
    wait_for_loading_complete,
    click_button,
    expect_url_contains,
)

SARAH_EMAIL = "demo+sarah@fiscalguard.app"
SARAH_PASSWORD = "demo123"


@pytest.fixture
def sarah_page(page: Page, base_url: str):
    """Authenticated page for Sarah"""
    setup_authenticated_session(page, SARAH_EMAIL, SARAH_PASSWORD)
    page.goto(base_url)
    wait_for_loading_complete(page)
    return page


class TestSarahShoppingAddiction:
    """Test suite for Sarah's shopping addiction scenario"""

    def test_should_show_over_budget_warnings_on_dashboard(self, sarah_page: Page):
        """Verify over-budget warnings are displayed on Dashboard"""
        # Navigate to Dashboard
        sarah_page.click('[href="/"]')
        wait_for_loading_complete(sarah_page)

        # Check for Guard Score
        guard_score = sarah_page.locator('text=Guard Score')
        expect(guard_score).to_be_visible()

        # Check for allocation health warnings
        allocation_health = sarah_page.locator('text=Allocation Health')
        expect(allocation_health).to_be_visible()

        # Shopping category should show over-budget
        shopping = sarah_page.locator('text=Shopping').first
        expect(shopping).to_be_visible()

        # Should see "Over Budget" or "Near Capacity" status
        over_budget = sarah_page.locator('text=/Over Budget|Near Capacity/i')
        expect(over_budget.first).to_be_visible()

    def test_should_display_regret_patterns_in_insights(self, sarah_page: Page):
        """Verify regret patterns are shown in Insights page"""
        # Navigate to Insights
        sarah_page.click('text=Insights')
        expect_url_contains(sarah_page, '/insights')
        wait_for_loading_complete(sarah_page)

        # Check for Peace of Mind Score
        peace_of_mind = sarah_page.locator('text=Peace of Mind Score')
        expect(peace_of_mind).to_be_visible()

        # Check for reflections section
        reflections = sarah_page.locator('text=Reflections')
        expect(reflections).to_be_visible()

        # Should see past decisions
        designer_shoes = sarah_page.locator('text=Designer Shoes')
        expect(designer_shoes).to_be_visible()

        # Should see high regret indicators
        regret_icon = sarah_page.locator('svg').filter(has=sarah_page.locator('[class*="frown"]'))
        # At least one regret indicator should be visible
        count = regret_icon.count()
        assert count > 0

    def test_should_allow_rating_satisfaction_on_past_decisions(self, sarah_page: Page):
        """Verify ability to rate satisfaction on past decisions"""
        # Navigate to Insights
        sarah_page.click('text=Insights')
        wait_for_loading_complete(sarah_page)

        # Find a decision without feedback (if any)
        satisfaction_section = sarah_page.locator('text=Rate Satisfaction').first

        if satisfaction_section.is_visible():
            # Click on a satisfaction icon (e.g., middle one for neutral)
            satisfaction_icons = sarah_page.locator('button').filter(
                has=sarah_page.locator('svg')
            )

            # Click the first available satisfaction icon
            satisfaction_icons.first.click()

            # Wait for the feedback to be submitted
            sarah_page.wait_for_timeout(1000)

            # The label should change from "Rate Satisfaction" to "Satisfaction"
            updated_label = sarah_page.locator('text=Satisfaction').first
            expect(updated_label).to_be_visible(timeout=5000)

    def test_should_get_strict_recommendation_from_financial_monk_agent(self, sarah_page: Page):
        """Verify Financial Monk agent provides strict recommendations"""
        # Navigate to Agent Chat
        sarah_page.click('text=Shield')
        expect_url_contains(sarah_page, '/chat')
        wait_for_loading_complete(sarah_page)

        # Type a purchase request
        input_field = sarah_page.locator('input[placeholder*="purchase" i], textarea[placeholder*="purchase" i]')
        input_field.fill('Should I buy designer boots for $450?')

        # Send message
        click_button(sarah_page, 'Send')

        # Wait for agent response
        sarah_page.wait_for_selector('text=/analyzing|agent/i', timeout=30000)
        wait_for_loading_complete(sarah_page)

        # Should see agent's response
        agent_response = sarah_page.locator('[class*="agent"], [class*="assistant"]').last
        expect(agent_response).to_be_visible(timeout=30000)

        # Response should be visible (Financial Monk persona should be strict)
        response_text = agent_response.text_content()
        assert response_text is not None
        assert len(response_text) > 20

    def test_should_show_emergency_fund_goal_progress(self, sarah_page: Page):
        """Verify Emergency Fund goal progress is displayed"""
        # Navigate to Vault
        sarah_page.click('text=Vault')
        expect_url_contains(sarah_page, '/vault')
        wait_for_loading_complete(sarah_page)

        # Switch to Goals tab
        click_button(sarah_page, 'Goals')
        sarah_page.wait_for_timeout(500)

        # Check for Emergency Fund
        emergency_fund = sarah_page.locator('text=Emergency Fund')
        expect(emergency_fund).to_be_visible()

        # Should see progress indicator
        progress = sarah_page.locator('text=/2,?800|2800/')  # Current amount
        expect(progress).to_be_visible()

    def test_should_allow_adding_progress_to_goals(self, sarah_page: Page):
        """Verify ability to add progress to goals"""
        # Navigate to Vault
        sarah_page.click('text=Vault')
        click_button(sarah_page, 'Goals')
        wait_for_loading_complete(sarah_page)

        # Find "Add $" button
        add_button = sarah_page.locator('button:has-text("Add $")').first
        expect(add_button).to_be_visible()

        # Click to open modal
        add_button.click()

        # Modal should appear
        modal = sarah_page.locator('text=Add Progress')
        expect(modal).to_be_visible()

        # Fill in amount
        amount_input = sarah_page.locator('input[type="number"]')
        amount_input.fill('100')

        # Click Add Progress button
        click_button(sarah_page, 'Add Progress')

        # Wait for modal to close and data to refresh
        sarah_page.wait_for_timeout(2000)
        wait_for_loading_complete(sarah_page)

        # Amount should be updated (2800 + 100 = 2900)
        updated_amount = sarah_page.locator('text=/2,?900|2900/')
        expect(updated_amount).to_be_visible(timeout=5000)

    def test_should_show_persona_settings_in_setup(self, sarah_page: Page):
        """Verify persona settings are shown in Setup page"""
        # Navigate to Setup
        sarah_page.click('text=Setup')
        expect_url_contains(sarah_page, '/setup')
        wait_for_loading_complete(sarah_page)

        # Click on Guard Strictness
        sarah_page.click('text=Guard Strictness')
        expect_url_contains(sarah_page, '/setup/agent')

        # Should see Financial Monk persona
        financial_monk = sarah_page.locator('text=Financial Monk')
        expect(financial_monk).to_be_visible()

        # Should see strictness slider at high value
        strictness_indicator = sarah_page.locator('text=/9.*%|90%/i')
        expect(strictness_indicator).to_be_visible()

    def test_full_user_journey(self, sarah_page: Page):
        """Complete user journey: check budget → ask agent → view insights"""
        # 1. Start at Dashboard
        sarah_page.click('[href="/"]')
        wait_for_loading_complete(sarah_page)

        # Verify over-budget status
        over_budget = sarah_page.locator('text=/Over Budget/i')
        expect(over_budget.first).to_be_visible()

        # 2. Go to Agent Chat
        sarah_page.click('text=Shield')
        wait_for_loading_complete(sarah_page)

        # Ask about a purchase
        input_field = sarah_page.locator('input, textarea').last
        input_field.fill('Should I buy a $200 dress?')
        click_button(sarah_page, 'Send')

        # Wait for response
        sarah_page.wait_for_timeout(5000)

        # 3. Go to Insights to review patterns
        sarah_page.click('text=Insights')
        wait_for_loading_complete(sarah_page)

        # Verify reflections are visible
        reflections = sarah_page.locator('text=Reflections')
        expect(reflections).to_be_visible()

        # 4. Check Vault goals
        sarah_page.click('text=Vault')
        click_button(sarah_page, 'Goals')
        wait_for_loading_complete(sarah_page)

        # Verify Emergency Fund goal
        emergency_fund = sarah_page.locator('text=Emergency Fund')
        expect(emergency_fund).to_be_visible()
