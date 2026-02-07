"""Tests for decision service."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.models import Base
from core.database.models import PurchaseDecision as PurchaseDecisionDB
from core.models.decision import (
    BudgetAnalysis,
    DecisionAnalysis,
    DecisionFeedback,
    DecisionScore,
    GoalAnalysis,
    PurchaseCategory,
    PurchaseDecision,
    PurchaseDecisionRequest,
)
from core.services.decision import DecisionService


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
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
def mock_decision_agent():
    """Create a mock decision agent."""
    return MagicMock()


@pytest.fixture
def decision_service(db_session, mock_decision_agent):
    """Create a decision service instance with mocked agent."""
    service = DecisionService(db_session)
    service.agent = mock_decision_agent
    return service


@pytest.fixture
def sample_purchase_request():
    """Create a sample purchase request."""
    return PurchaseDecisionRequest(
        item_name="New Laptop",
        amount=Decimal("1200.00"),
        category="electronics",
        reason="Need for work",
        urgency="medium",
    )


@pytest.fixture
def sample_decision():
    """Create a sample purchase decision response."""
    return PurchaseDecision(
        score=7,
        decision_category=DecisionScore.MILD_YES,
        reasoning="This is a reasonable purchase for work needs.",
        analysis=DecisionAnalysis(
            budget_analysis=BudgetAnalysis(
                category="electronics",
                current_spent=500.00,  # Use float instead of Decimal
                limit=2000.00,  # Use float instead of Decimal
                remaining=1500.00,  # Use float instead of Decimal
                percentage_used=25.0,
                would_exceed=False,
                impact_description="Within budget limits",
            ),
            affected_goals=[],
            purchase_category=PurchaseCategory.DISCRETIONARY,
            financial_health_score=75.0,
        ),
        alternatives=["Consider refurbished laptop", "Wait for Black Friday sales"],
        conditions=["If you can get 20% discount", "If current laptop is broken"],
    )


class TestCreateDecision:
    """Tests for creating purchase decisions."""

    def test_create_decision_success(
        self,
        decision_service,
        user_id,
        sample_purchase_request,
        sample_decision,
    ):
        """Test successful decision creation."""
        # Mock the agent's response
        decision_service.agent.analyze_purchase.return_value = sample_decision

        result = decision_service.create_decision(user_id, sample_purchase_request)

        assert result is not None
        assert result.decision == sample_decision
        assert result.decision_id is not None
        assert decision_service.agent.analyze_purchase.called

    def test_create_decision_saves_to_database(
        self,
        decision_service,
        user_id,
        sample_purchase_request,
        sample_decision,
    ):
        """Test that decision is saved to database."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        result = decision_service.create_decision(user_id, sample_purchase_request)

        # Verify it was saved
        db_decision = (
            decision_service.db.query(PurchaseDecisionDB)
            .filter(PurchaseDecisionDB.decision_id == result.decision_id)
            .first()
        )

        assert db_decision is not None
        assert db_decision.user_id == user_id
        assert db_decision.item_name == "New Laptop"
        assert db_decision.amount == Decimal("1200.00")
        assert db_decision.score == 7
        assert db_decision.decision_category == DecisionScore.MILD_YES.value

    def test_create_decision_with_minimal_request(
        self, decision_service, user_id, sample_decision
    ):
        """Test creating decision with minimal request data."""
        minimal_request = PurchaseDecisionRequest(
            item_name="Coffee",
            amount=Decimal("5.00"),
        )

        decision_service.agent.analyze_purchase.return_value = sample_decision

        result = decision_service.create_decision(user_id, minimal_request)

        assert result is not None
        assert result.decision_id is not None

    def test_create_decision_calls_agent_with_correct_params(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test that agent is called with correct parameters."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        decision_service.create_decision(user_id, sample_purchase_request)

        decision_service.agent.analyze_purchase.assert_called_once_with(
            user_id, sample_purchase_request, None
        )

    def test_create_decision_strong_no(self, decision_service, user_id):
        """Test creating decision with strong no recommendation."""
        request = PurchaseDecisionRequest(
            item_name="Luxury Watch",
            amount=Decimal("5000.00"),
            category="luxury",
            reason="Want it",
            urgency="low",
        )

        strong_no_decision = PurchaseDecision(
            score=2,
            decision_category=DecisionScore.STRONG_NO,
            reasoning="This purchase would significantly harm your financial goals.",
            analysis=DecisionAnalysis(
                purchase_category=PurchaseCategory.IMPULSE,
                financial_health_score=35.0,
            ),
            alternatives=["Save the money", "Look for cheaper alternatives"],
            conditions=["Only if you have extra windfall income"],
        )

        decision_service.agent.analyze_purchase.return_value = strong_no_decision

        result = decision_service.create_decision(user_id, request)

        assert result.decision.score == 2
        assert result.decision.decision_category == DecisionScore.STRONG_NO

    def test_create_decision_strong_yes(self, decision_service, user_id):
        """Test creating decision with strong yes recommendation."""
        request = PurchaseDecisionRequest(
            item_name="Groceries",
            amount=Decimal("150.00"),
            category="groceries",
            urgency="high",
        )

        strong_yes_decision = PurchaseDecision(
            score=10,
            decision_category=DecisionScore.STRONG_YES,
            reasoning="Essential purchase within budget.",
            analysis=DecisionAnalysis(
                purchase_category=PurchaseCategory.ESSENTIAL,
                financial_health_score=85.0,
            ),
        )

        decision_service.agent.analyze_purchase.return_value = strong_yes_decision

        result = decision_service.create_decision(user_id, request)

        assert result.decision.score == 10
        assert result.decision.decision_category == DecisionScore.STRONG_YES


class TestGetDecision:
    """Tests for retrieving decisions."""

    def test_get_decision_success(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test retrieving an existing decision."""
        # Create a decision first
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        # Retrieve it
        retrieved = decision_service.get_decision(user_id, created.decision_id)

        assert retrieved is not None
        assert retrieved.id == created.decision_id
        assert retrieved.user_id == user_id
        assert retrieved.item_name == "New Laptop"

    def test_get_decision_not_found(self, decision_service, user_id):
        """Test retrieving non-existent decision."""
        decision = decision_service.get_decision(user_id, uuid4())

        assert decision is None

    def test_get_decision_wrong_user(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test that user can't access another user's decision."""
        # Create decision for user_id
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        # Try to access with different user
        different_user_id = uuid4()
        retrieved = decision_service.get_decision(
            different_user_id, created.decision_id
        )

        assert retrieved is None


class TestListDecisions:
    """Tests for listing decisions."""

    def test_list_decisions_empty(self, decision_service, user_id):
        """Test listing decisions when user has none."""
        decisions = decision_service.list_decisions(user_id)

        assert decisions == []

    def test_list_decisions_multiple(self, decision_service, user_id, sample_decision):
        """Test listing multiple decisions."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 3 decisions
        for i in range(3):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user_id, request)

        decisions = decision_service.list_decisions(user_id)

        assert len(decisions) == 3
        # Should be ordered by most recent first
        assert decisions[0].item_name == "Item 3"
        assert decisions[2].item_name == "Item 1"

    def test_list_decisions_pagination(
        self, decision_service, user_id, sample_decision
    ):
        """Test pagination of decisions list."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 5 decisions
        for i in range(5):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user_id, request)

        # Get first page
        page1 = decision_service.list_decisions(user_id, limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = decision_service.list_decisions(user_id, limit=2, offset=2)
        assert len(page2) == 2

        # Ensure no overlap
        assert page1[0].id != page2[0].id

    def test_list_decisions_default_limit(
        self, decision_service, user_id, sample_decision
    ):
        """Test default limit of 50 decisions."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 60 decisions
        for i in range(60):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user_id, request)

        decisions = decision_service.list_decisions(user_id)

        # Should only return default limit of 50
        assert len(decisions) == 50

    def test_list_decisions_isolation(self, decision_service, user_id, sample_decision):
        """Test that users only see their own decisions."""
        user1_id = user_id
        user2_id = uuid4()

        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create decisions for both users
        request = PurchaseDecisionRequest(
            item_name="Test Item",
            amount=Decimal("100.00"),
        )

        decision_service.create_decision(user1_id, request)
        decision_service.create_decision(user2_id, request)

        user1_decisions = decision_service.list_decisions(user1_id)
        user2_decisions = decision_service.list_decisions(user2_id)

        assert len(user1_decisions) == 1
        assert len(user2_decisions) == 1
        assert user1_decisions[0].user_id != user2_decisions[0].user_id


class TestAddFeedback:
    """Tests for adding feedback to decisions."""

    def test_add_feedback_success(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test successfully adding feedback."""
        # Create decision
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        # Add feedback
        feedback = DecisionFeedback(
            actual_purchase=True,
            regret_level=3,
            feedback="Good purchase, but slightly expensive",
        )

        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)

        assert updated is not None
        assert updated.actual_purchase is True
        assert updated.regret_level == 3
        assert updated.user_feedback == "Good purchase, but slightly expensive"

    def test_add_feedback_not_purchased(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test adding feedback when item wasn't purchased."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        feedback = DecisionFeedback(
            actual_purchase=False,
            feedback="Decided to wait for better deal",
        )

        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)

        assert updated.actual_purchase is False
        assert updated.regret_level is None

    def test_add_feedback_high_regret(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test adding feedback with high regret level."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        feedback = DecisionFeedback(
            actual_purchase=True,
            regret_level=10,
            feedback="Terrible decision, totally regret it",
        )

        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)

        assert updated.regret_level == 10

    def test_add_feedback_no_regret(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test adding feedback with no regret."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        feedback = DecisionFeedback(
            actual_purchase=True,
            regret_level=1,
            feedback="Great purchase, very happy",
        )

        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)

        assert updated.regret_level == 1

    def test_add_feedback_decision_not_found(self, decision_service, user_id):
        """Test adding feedback to non-existent decision."""
        feedback = DecisionFeedback(actual_purchase=True, regret_level=5)

        result = decision_service.add_feedback(user_id, uuid4(), feedback)

        assert result is None

    def test_add_feedback_wrong_user(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test that user can't add feedback to another user's decision."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        different_user_id = uuid4()
        feedback = DecisionFeedback(actual_purchase=True, regret_level=5)

        result = decision_service.add_feedback(
            different_user_id, created.decision_id, feedback
        )

        assert result is None

    def test_add_feedback_minimal(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test adding minimal feedback (only purchase status)."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        feedback = DecisionFeedback(actual_purchase=False)

        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)

        assert updated.actual_purchase is False
        assert updated.regret_level is None
        assert updated.user_feedback is None

    def test_add_feedback_update_existing(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test updating existing feedback."""
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)

        # Add initial feedback
        feedback1 = DecisionFeedback(actual_purchase=True, regret_level=5)
        decision_service.add_feedback(user_id, created.decision_id, feedback1)

        # Update feedback
        feedback2 = DecisionFeedback(actual_purchase=True, regret_level=8)
        updated = decision_service.add_feedback(user_id, created.decision_id, feedback2)

        # Should be updated, not added as new
        assert updated.regret_level == 8


class TestGetDecisionStats:
    """Tests for getting decision statistics."""

    def test_get_stats_no_decisions(self, decision_service, user_id):
        """Test statistics when user has no decisions."""
        stats = decision_service.get_decision_stats(user_id)

        assert stats["total_decisions"] == 0
        assert stats["average_score"] == 0.0
        assert stats["total_requested"] == 0.0
        assert stats["decisions_by_category"] == {}
        assert stats["feedback_rate"] == 0.0

    def test_get_stats_with_decisions(self, decision_service, user_id, sample_decision):
        """Test statistics with multiple decisions."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 3 decisions with different scores
        for i, score in enumerate([5, 7, 9]):
            sample_decision.score = score
            sample_decision.decision_category = DecisionScore.MILD_YES
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal(f"{100 * (i + 1)}.00"),
            )
            decision_service.create_decision(user_id, request)

        stats = decision_service.get_decision_stats(user_id)

        assert stats["total_decisions"] == 3
        assert stats["average_score"] == 7.0  # (5+7+9)/3
        assert stats["total_requested"] == 600.0  # 100+200+300

    def test_get_stats_decisions_by_category(
        self, decision_service, user_id, sample_decision
    ):
        """Test grouping decisions by category."""
        # Create decisions with different categories
        categories = [
            DecisionScore.STRONG_YES,
            DecisionScore.MILD_YES,
            DecisionScore.MILD_YES,
            DecisionScore.NEUTRAL,
        ]

        for i, category in enumerate(categories):
            sample_decision.score = 7
            sample_decision.decision_category = category
            decision_service.agent.analyze_purchase.return_value = sample_decision

            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user_id, request)

        stats = decision_service.get_decision_stats(user_id)

        assert stats["decisions_by_category"]["strong_yes"] == 1
        assert stats["decisions_by_category"]["mild_yes"] == 2
        assert stats["decisions_by_category"]["neutral"] == 1

    def test_get_stats_feedback_rate(self, decision_service, user_id, sample_decision):
        """Test feedback rate calculation."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 4 decisions
        decisions = []
        for i in range(4):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            result = decision_service.create_decision(user_id, request)
            decisions.append(result)

        # Add feedback to 2 of them (50%)
        for i in range(2):
            feedback = DecisionFeedback(actual_purchase=True, regret_level=5)
            decision_service.add_feedback(user_id, decisions[i].decision_id, feedback)

        stats = decision_service.get_decision_stats(user_id)

        assert stats["feedback_rate"] == 50.0

    def test_get_stats_feedback_rate_zero(
        self, decision_service, user_id, sample_decision
    ):
        """Test feedback rate when no feedback given."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create decisions without feedback
        for i in range(3):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user_id, request)

        stats = decision_service.get_decision_stats(user_id)

        assert stats["feedback_rate"] == 0.0

    def test_get_stats_feedback_rate_full(
        self, decision_service, user_id, sample_decision
    ):
        """Test feedback rate when all have feedback."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 3 decisions
        for i in range(3):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal("100.00"),
            )
            result = decision_service.create_decision(user_id, request)

            # Add feedback to all
            feedback = DecisionFeedback(actual_purchase=True, regret_level=5)
            decision_service.add_feedback(user_id, result.decision_id, feedback)

        stats = decision_service.get_decision_stats(user_id)

        assert stats["feedback_rate"] == 100.0

    def test_get_stats_isolation(self, decision_service, user_id, sample_decision):
        """Test that stats only include user's own decisions."""
        user1_id = user_id
        user2_id = uuid4()

        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 2 decisions for user1
        for i in range(2):
            request = PurchaseDecisionRequest(
                item_name=f"User1 Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user1_id, request)

        # Create 3 decisions for user2
        for i in range(3):
            request = PurchaseDecisionRequest(
                item_name=f"User2 Item {i + 1}",
                amount=Decimal("100.00"),
            )
            decision_service.create_decision(user2_id, request)

        user1_stats = decision_service.get_decision_stats(user1_id)
        user2_stats = decision_service.get_decision_stats(user2_id)

        assert user1_stats["total_decisions"] == 2
        assert user2_stats["total_decisions"] == 3


class TestDecisionServiceIntegration:
    """Integration tests for decision service."""

    def test_complete_decision_flow(
        self, decision_service, user_id, sample_purchase_request, sample_decision
    ):
        """Test complete flow: create, retrieve, add feedback, get stats."""
        # Create decision
        decision_service.agent.analyze_purchase.return_value = sample_decision
        created = decision_service.create_decision(user_id, sample_purchase_request)
        assert created is not None

        # Retrieve decision
        retrieved = decision_service.get_decision(user_id, created.decision_id)
        assert retrieved is not None
        assert retrieved.id == created.decision_id

        # Add feedback
        feedback = DecisionFeedback(actual_purchase=True, regret_level=4)
        updated = decision_service.add_feedback(user_id, created.decision_id, feedback)
        assert updated.actual_purchase is True

        # Get stats
        stats = decision_service.get_decision_stats(user_id)
        assert stats["total_decisions"] == 1
        assert stats["feedback_rate"] == 100.0

    def test_multiple_decisions_with_varied_feedback(
        self, decision_service, user_id, sample_decision
    ):
        """Test realistic scenario with multiple decisions and varied feedback."""
        decision_service.agent.analyze_purchase.return_value = sample_decision

        # Create 5 decisions
        decision_ids = []
        for i in range(5):
            request = PurchaseDecisionRequest(
                item_name=f"Item {i + 1}",
                amount=Decimal(f"{50 * (i + 1)}.00"),
                category="general",
            )
            result = decision_service.create_decision(user_id, request)
            decision_ids.append(result.decision_id)

        # Add varied feedback to 3 of them
        feedbacks = [
            DecisionFeedback(actual_purchase=True, regret_level=2),  # Good
            DecisionFeedback(actual_purchase=True, regret_level=8),  # Regret
            DecisionFeedback(actual_purchase=False),  # Didn't buy
        ]

        for i, feedback in enumerate(feedbacks):
            decision_service.add_feedback(user_id, decision_ids[i], feedback)

        # Verify list shows all
        decisions = decision_service.list_decisions(user_id)
        assert len(decisions) == 5

        # Verify stats
        stats = decision_service.get_decision_stats(user_id)
        assert stats["total_decisions"] == 5
        assert stats["feedback_rate"] == 60.0  # 3 out of 5
