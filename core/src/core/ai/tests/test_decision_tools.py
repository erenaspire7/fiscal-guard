"""Tests for decision tools."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.ai.decision_tools import create_decision_tools
from core.database.models import Base, Budget, Goal, PurchaseDecision


# Test database setup
@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    # Use in-memory SQLite for tests
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def user_id():
    """Generate a test user ID."""
    return uuid4()


@pytest.fixture
def sample_budget(db_session: Session, user_id):
    """Create a sample budget for testing."""
    today = date.today()
    budget = Budget(
        user_id=user_id,
        name="Test Budget",
        total_monthly=Decimal("3000.00"),
        period_start=today.replace(day=1),
        period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1)
        - timedelta(days=1),
        categories={
            "groceries": {"limit": 500, "spent": 250},
            "clothing": {"limit": 200, "spent": 180},
            "entertainment": {"limit": 150, "spent": 50},
            "rent": {"limit": 1500, "spent": 1500},
        },
    )
    db_session.add(budget)
    db_session.commit()
    return budget


@pytest.fixture
def sample_goals(db_session: Session, user_id):
    """Create sample goals for testing."""
    goals = [
        Goal(
            user_id=user_id,
            goal_name="Emergency Fund",
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("2000.00"),
            priority="high",
            deadline=date.today() + timedelta(days=180),
            is_completed=False,
        ),
        Goal(
            user_id=user_id,
            goal_name="Vacation",
            target_amount=Decimal("2000.00"),
            current_amount=Decimal("500.00"),
            priority="medium",
            deadline=date.today() + timedelta(days=90),
            is_completed=False,
        ),
        Goal(
            user_id=user_id,
            goal_name="New Laptop",
            target_amount=Decimal("1500.00"),
            current_amount=Decimal("1500.00"),
            priority="low",
            deadline=date.today() - timedelta(days=10),
            is_completed=True,
        ),
    ]
    for goal in goals:
        db_session.add(goal)
    db_session.commit()
    return goals


@pytest.fixture
def sample_decisions(db_session: Session, user_id):
    """Create sample purchase decisions for testing."""
    decisions = [
        PurchaseDecision(
            user_id=user_id,
            item_name="Designer jeans",
            amount=Decimal("250.00"),
            category="clothing",
            score=3,
            decision_category="strong_no",
            reasoning="Over budget",
            analysis={},
            actual_purchase=True,
            regret_level=8,
            created_at=datetime.now() - timedelta(days=30),
        ),
        PurchaseDecision(
            user_id=user_id,
            item_name="Fancy dinner",
            amount=Decimal("120.00"),
            category="entertainment",
            score=4,
            decision_category="mild_no",
            reasoning="Expensive",
            analysis={},
            actual_purchase=True,
            regret_level=6,
            created_at=datetime.now() - timedelta(days=20),
        ),
        PurchaseDecision(
            user_id=user_id,
            item_name="Groceries",
            amount=Decimal("80.00"),
            category="groceries",
            score=9,
            decision_category="strong_yes",
            reasoning="Within budget",
            analysis={},
            actual_purchase=True,
            regret_level=0,
            created_at=datetime.now() - timedelta(days=10),
        ),
        PurchaseDecision(
            user_id=user_id,
            item_name="Concert ticket",
            amount=Decimal("60.00"),
            category="entertainment",
            score=7,
            decision_category="mild_yes",
            reasoning="Good value",
            analysis={},
            actual_purchase=False,
            regret_level=None,
            created_at=datetime.now() - timedelta(days=5),
        ),
    ]
    for decision in decisions:
        db_session.add(decision)
    db_session.commit()
    return decisions


class TestCheckBudget:
    """Tests for check_budget tool."""

    def test_check_budget_within_limit(self, db_session, user_id, sample_budget):
        """Test checking a purchase within budget."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        result = check_budget(user_id=str(user_id), category="groceries", amount=100.0)

        assert result["has_budget"] is True
        assert result["category"] == "groceries"
        assert result["current_spent"] == 250.0
        assert result["limit"] == 500.0
        assert result["remaining"] == 250.0
        assert result["would_exceed"] is False
        assert "comfortably within" in result["impact_description"].lower()

    def test_check_budget_would_exceed(self, db_session, user_id, sample_budget):
        """Test checking a purchase that would exceed budget."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        result = check_budget(user_id=str(user_id), category="clothing", amount=100.0)

        assert result["has_budget"] is True
        assert result["would_exceed"] is True
        assert result["current_spent"] == 180.0
        assert result["limit"] == 200.0
        assert "over budget" in result["impact_description"].lower()

    def test_check_budget_no_budget(self, db_session, user_id):
        """Test checking budget when user has no budget."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        result = check_budget(user_id=str(user_id), category="groceries", amount=100.0)

        assert result["has_budget"] is False
        assert "no active budget" in result["impact_description"].lower()

    def test_check_budget_category_not_found(self, db_session, user_id, sample_budget):
        """Test checking a category that doesn't exist in budget."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        result = check_budget(user_id=str(user_id), category="travel", amount=500.0)

        assert result["has_budget"] is False
        assert "not found in budget" in result["impact_description"].lower()

    def test_check_budget_invalid_user_id(self, db_session):
        """Test with invalid user ID format."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        result = check_budget(
            user_id="invalid-uuid", category="groceries", amount=100.0
        )

        assert result["has_budget"] is False
        assert "invalid user id" in result["impact_description"].lower()

    def test_check_budget_high_percentage(self, db_session, user_id, sample_budget):
        """Test checking budget when nearing limit."""
        tools = create_decision_tools(db_session)
        check_budget = tools[0]

        # Clothing is at 180/200 = 90%, adding 10 would be 190/200 = 95%
        result = check_budget(user_id=str(user_id), category="clothing", amount=10.0)

        assert result["has_budget"] is True
        assert result["would_exceed"] is False
        assert result["percentage_used"] > 80
        assert "within budget" in result["impact_description"].lower()


class TestCheckGoals:
    """Tests for check_goals tool."""

    def test_check_goals_with_goals(self, db_session, user_id, sample_goals):
        """Test checking goals when user has goals."""
        tools = create_decision_tools(db_session)
        check_goals = tools[1]

        result = check_goals(user_id=str(user_id))

        assert result["total_goals"] == 2  # Only active goals
        assert result["active_goals"] == 2
        assert result["total_target"] == 7000.0  # 5000 + 2000
        assert result["total_current"] == 2500.0  # 2000 + 500
        assert result["total_remaining"] == 4500.0
        assert len(result["goals"]) == 2
        assert "high-priority" in result["impact_description"].lower()

    def test_check_goals_no_goals(self, db_session, user_id):
        """Test checking goals when user has no goals."""
        tools = create_decision_tools(db_session)
        check_goals = tools[1]

        result = check_goals(user_id=str(user_id))

        assert result["total_goals"] == 0
        assert result["active_goals"] == 0
        assert result["total_target"] == 0.0
        assert result["total_current"] == 0.0
        assert "no active financial goals" in result["impact_description"].lower()

    def test_check_goals_invalid_user_id(self, db_session):
        """Test with invalid user ID."""
        tools = create_decision_tools(db_session)
        check_goals = tools[1]

        result = check_goals(user_id="invalid-uuid")

        assert result["total_goals"] == 0
        assert "invalid user id" in result["impact_description"].lower()

    def test_check_goals_structure(self, db_session, user_id, sample_goals):
        """Test the structure of returned goals."""
        tools = create_decision_tools(db_session)
        check_goals = tools[1]

        result = check_goals(user_id=str(user_id))

        goals = result["goals"]
        assert len(goals) > 0

        first_goal = goals[0]
        assert "name" in first_goal
        assert "target" in first_goal
        assert "current" in first_goal
        assert "remaining" in first_goal
        assert "percentage" in first_goal
        assert "priority" in first_goal


class TestAnalyzeSpending:
    """Tests for analyze_spending tool."""

    def test_analyze_spending_with_budget(self, db_session, user_id, sample_budget):
        """Test spending analysis with active budget."""
        tools = create_decision_tools(db_session)
        analyze_spending = tools[2]

        result = analyze_spending(user_id=str(user_id))

        assert result["total_budget"] == 3000.0
        # Total spent: 250 + 180 + 50 + 1500 = 1980
        assert result["total_spent"] == 1980.0
        assert result["total_remaining"] == 1020.0
        assert result["percentage_spent"] == 66.0
        assert 0 <= result["financial_health_score"] <= 100
        assert len(result["analysis_description"]) > 0

    def test_analyze_spending_no_budget(self, db_session, user_id):
        """Test spending analysis with no budget."""
        tools = create_decision_tools(db_session)
        analyze_spending = tools[2]

        result = analyze_spending(user_id=str(user_id))

        assert result["total_budget"] == 0.0
        assert result["total_spent"] == 0.0
        assert "no active budget" in result["analysis_description"].lower()

    def test_analyze_spending_health_score_calculation(
        self, db_session, user_id, sample_budget, sample_goals
    ):
        """Test that financial health score is calculated."""
        tools = create_decision_tools(db_session)
        analyze_spending = tools[2]

        result = analyze_spending(user_id=str(user_id))

        # Health score should be a reasonable value
        assert 0 <= result["financial_health_score"] <= 100
        # With 66% spent, should have decent score
        assert result["financial_health_score"] > 30

    def test_analyze_spending_health_descriptions(
        self, db_session, user_id, sample_budget
    ):
        """Test that appropriate health descriptions are generated."""
        tools = create_decision_tools(db_session)
        analyze_spending = tools[2]

        result = analyze_spending(user_id=str(user_id))

        description = result["analysis_description"].lower()

        # Should mention the percentage spent
        assert "66" in description or "1980" in description

        # Should have health status
        assert any(
            status in description
            for status in ["excellent", "good", "fair", "concerning"]
        )


class TestCheckPastDecisions:
    """Tests for check_past_decisions tool."""

    def test_check_past_decisions_all(self, db_session, user_id, sample_decisions):
        """Test retrieving all past decisions."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(user_id=str(user_id), limit=10)

        assert result["total_decisions"] == 4
        assert len(result["decisions"]) == 4
        assert result["average_score"] > 0
        assert len(result["category_patterns"]) > 0

    def test_check_past_decisions_by_category(
        self, db_session, user_id, sample_decisions
    ):
        """Test filtering decisions by category."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(
            user_id=str(user_id), category="entertainment", limit=10
        )

        assert result["total_decisions"] == 2
        assert all(d["category"] == "entertainment" for d in result["decisions"])

    def test_check_past_decisions_by_amount_range(
        self, db_session, user_id, sample_decisions
    ):
        """Test filtering decisions by amount range."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(
            user_id=str(user_id), min_amount=100.0, max_amount=200.0, limit=10
        )

        assert result["total_decisions"] == 1  # Only fancy dinner at $120
        assert result["decisions"][0]["amount"] == 120.0

    def test_check_past_decisions_limit(self, db_session, user_id, sample_decisions):
        """Test that limit parameter works."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(user_id=str(user_id), limit=2)

        assert len(result["decisions"]) == 2
        # Should be ordered by most recent
        assert result["decisions"][0]["item"] == "Concert ticket"

    def test_check_past_decisions_no_decisions(self, db_session, user_id):
        """Test when user has no past decisions."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(user_id=str(user_id))

        assert result["total_decisions"] == 0
        assert len(result["decisions"]) == 0
        assert "no past decisions" in result["insights"].lower()

    def test_check_past_decisions_insights(self, db_session, user_id, sample_decisions):
        """Test that insights are generated."""
        tools = create_decision_tools(db_session)
        check_past_decisions = tools[3]

        result = check_past_decisions(user_id=str(user_id))

        insights = result["insights"]
        assert len(insights) > 0
        # Should identify patterns
        assert "entertainment" in insights.lower() or "clothing" in insights.lower()


class TestAnalyzeRegrets:
    """Tests for analyze_regrets tool."""

    def test_analyze_regrets_with_regrets(self, db_session, user_id, sample_decisions):
        """Test regret analysis with regretted purchases."""
        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id))

        assert result["total_purchases"] == 4
        assert (
            result["purchases_with_feedback"] == 4
        )  # All 4 have actual_purchase set (including the one with False)
        assert result["regretted_purchases"] == 2  # Jeans (8) and dinner (6)
        assert result["regret_rate"] > 0
        assert result["average_regret_level"] > 0

    def test_analyze_regrets_by_category(self, db_session, user_id, sample_decisions):
        """Test regret analysis filtered by category."""
        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id), category="clothing")

        assert result["total_purchases"] == 1
        assert result["regretted_purchases"] == 1
        assert result["regret_rate"] == 100.0

    def test_analyze_regrets_no_regrets(self, db_session, user_id):
        """Test when user has no purchase history."""
        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id))

        assert result["total_purchases"] == 0
        assert result["regretted_purchases"] == 0
        assert "no purchase history" in result["recommendations"].lower()

    def test_analyze_regrets_patterns(self, db_session, user_id, sample_decisions):
        """Test that regret patterns are identified."""
        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id))

        patterns = result["common_regret_patterns"]
        assert len(patterns) > 0
        # Should identify that clothing has regrets
        assert any("clothing" in p.lower() for p in patterns)

    def test_analyze_regrets_recommendations(
        self, db_session, user_id, sample_decisions
    ):
        """Test that recommendations are provided."""
        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id))

        recommendations = result["recommendations"]
        assert len(recommendations) > 0
        # With 66% regret rate, should mention it
        assert "regret" in recommendations.lower()

    def test_analyze_regrets_no_feedback(self, db_session, user_id):
        """Test when user has decisions but no feedback."""
        # Create decisions without feedback
        decision = PurchaseDecision(
            user_id=user_id,
            item_name="Test item",
            amount=Decimal("100.00"),
            category="test",
            score=5,
            decision_category="neutral",
            reasoning="Test",
            analysis={},
            actual_purchase=None,
            regret_level=None,
        )
        db_session.add(decision)
        db_session.commit()

        tools = create_decision_tools(db_session)
        analyze_regrets = tools[4]

        result = analyze_regrets(user_id=str(user_id))

        assert result["total_purchases"] == 1
        assert result["purchases_with_feedback"] == 0
        assert "no purchase feedback" in result["recommendations"].lower()


class TestToolOutputSchemas:
    """Tests for tool output schema validation."""

    def test_all_tools_return_valid_schemas(self, db_session, user_id):
        """Test that all tools return outputs matching their schemas."""
        tools = create_decision_tools(db_session)

        # check_budget
        budget_result = tools[0](
            user_id=str(user_id), category="groceries", amount=100.0
        )
        assert isinstance(budget_result, dict)
        assert all(
            key in budget_result
            for key in [
                "category",
                "has_budget",
                "current_spent",
                "limit",
                "remaining",
                "percentage_used",
                "would_exceed",
                "impact_description",
            ]
        )

        # check_goals
        goals_result = tools[1](user_id=str(user_id))
        assert isinstance(goals_result, dict)
        assert all(
            key in goals_result
            for key in [
                "goals",
                "total_goals",
                "active_goals",
                "total_target",
                "total_current",
                "total_remaining",
                "impact_description",
            ]
        )

        # analyze_spending
        spending_result = tools[2](user_id=str(user_id))
        assert isinstance(spending_result, dict)
        assert all(
            key in spending_result
            for key in [
                "total_budget",
                "total_spent",
                "total_remaining",
                "percentage_spent",
                "financial_health_score",
                "analysis_description",
            ]
        )

        # check_past_decisions
        decisions_result = tools[3](user_id=str(user_id))
        assert isinstance(decisions_result, dict)
        assert all(
            key in decisions_result
            for key in [
                "decisions",
                "total_decisions",
                "average_score",
                "category_patterns",
                "insights",
            ]
        )

        # analyze_regrets
        regrets_result = tools[4](user_id=str(user_id))
        assert isinstance(regrets_result, dict)
        assert all(
            key in regrets_result
            for key in [
                "total_purchases",
                "purchases_with_feedback",
                "regretted_purchases",
                "regret_rate",
                "average_regret_level",
                "common_regret_patterns",
                "recommendations",
            ]
        )
