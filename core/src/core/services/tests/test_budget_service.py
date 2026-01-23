"""Tests for budget service."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.database.models import Base, Budget
from core.models.budget import BudgetCreate, BudgetUpdate, CategoryBudget
from core.services.budget import BudgetService


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
def budget_service(db_session):
    """Create a budget service instance."""
    return BudgetService(db_session)


@pytest.fixture
def sample_budget_data():
    """Create sample budget data."""
    today = date.today()
    return BudgetCreate(
        name="January Budget",
        total_monthly=Decimal("3000.00"),
        period_start=today.replace(day=1),
        period_end=(today.replace(day=1) + timedelta(days=32)).replace(day=1)
        - timedelta(days=1),
        categories={
            "groceries": CategoryBudget(limit=Decimal("500.00"), spent=Decimal("0")),
            "rent": CategoryBudget(limit=Decimal("1500.00"), spent=Decimal("0")),
            "entertainment": CategoryBudget(
                limit=Decimal("200.00"), spent=Decimal("0")
            ),
        },
    )


class TestCreateBudget:
    """Tests for creating budgets."""

    def test_create_budget_success(self, budget_service, user_id, sample_budget_data):
        """Test successful budget creation."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        assert budget is not None
        assert budget.budget_id is not None
        assert budget.user_id == user_id
        assert budget.name == "January Budget"
        assert budget.total_monthly == Decimal("3000.00")
        assert "groceries" in budget.categories
        assert budget.categories["groceries"]["limit"] == 500.0
        assert budget.created_at is not None

    def test_create_budget_with_multiple_categories(self, budget_service, user_id):
        """Test creating budget with many categories."""
        budget_data = BudgetCreate(
            name="Detailed Budget",
            total_monthly=Decimal("5000.00"),
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            categories={
                "groceries": CategoryBudget(limit=Decimal("500.00")),
                "rent": CategoryBudget(limit=Decimal("1500.00")),
                "utilities": CategoryBudget(limit=Decimal("300.00")),
                "transportation": CategoryBudget(limit=Decimal("400.00")),
                "entertainment": CategoryBudget(limit=Decimal("200.00")),
                "healthcare": CategoryBudget(limit=Decimal("300.00")),
                "savings": CategoryBudget(limit=Decimal("1800.00")),
            },
        )

        budget = budget_service.create_budget(user_id, budget_data)

        assert len(budget.categories) == 7
        assert budget.categories["savings"]["limit"] == 1800.0

    def test_create_budget_with_existing_spending(self, budget_service, user_id):
        """Test creating budget with pre-existing spending amounts."""
        budget_data = BudgetCreate(
            name="Mid-month Budget",
            total_monthly=Decimal("3000.00"),
            period_start=date.today(),
            period_end=date.today() + timedelta(days=15),
            categories={
                "groceries": CategoryBudget(
                    limit=Decimal("500.00"), spent=Decimal("250.00")
                ),
                "rent": CategoryBudget(
                    limit=Decimal("1500.00"), spent=Decimal("1500.00")
                ),
            },
        )

        budget = budget_service.create_budget(user_id, budget_data)

        assert budget.categories["groceries"]["spent"] == 250.0
        assert budget.categories["rent"]["spent"] == 1500.0


class TestGetBudget:
    """Tests for retrieving budgets."""

    def test_get_budget_success(self, budget_service, user_id, sample_budget_data):
        """Test retrieving an existing budget."""
        created_budget = budget_service.create_budget(user_id, sample_budget_data)

        retrieved_budget = budget_service.get_budget(created_budget.budget_id, user_id)

        assert retrieved_budget is not None
        assert retrieved_budget.budget_id == created_budget.budget_id
        assert retrieved_budget.name == created_budget.name

    def test_get_budget_not_found(self, budget_service, user_id):
        """Test retrieving a non-existent budget."""
        budget = budget_service.get_budget(uuid4(), user_id)

        assert budget is None

    def test_get_budget_wrong_user(self, budget_service, user_id, sample_budget_data):
        """Test that user can't access another user's budget."""
        created_budget = budget_service.create_budget(user_id, sample_budget_data)
        different_user_id = uuid4()

        budget = budget_service.get_budget(created_budget.budget_id, different_user_id)

        assert budget is None


class TestListBudgets:
    """Tests for listing budgets."""

    def test_list_budgets_empty(self, budget_service, user_id):
        """Test listing budgets when user has none."""
        budgets = budget_service.list_budgets(user_id)

        assert budgets == []

    def test_list_budgets_multiple(self, budget_service, user_id):
        """Test listing multiple budgets."""
        # Create 3 budgets
        for i in range(3):
            budget_data = BudgetCreate(
                name=f"Budget {i + 1}",
                total_monthly=Decimal("3000.00"),
                period_start=date.today(),
                period_end=date.today() + timedelta(days=30),
                categories={
                    "groceries": CategoryBudget(limit=Decimal("500.00")),
                },
            )
            budget_service.create_budget(user_id, budget_data)

        budgets = budget_service.list_budgets(user_id)

        assert len(budgets) == 3
        # Should be ordered by most recent first
        assert budgets[0].name == "Budget 3"
        assert budgets[2].name == "Budget 1"

    def test_list_budgets_pagination(self, budget_service, user_id):
        """Test pagination of budget list."""
        # Create 5 budgets
        for i in range(5):
            budget_data = BudgetCreate(
                name=f"Budget {i + 1}",
                total_monthly=Decimal("3000.00"),
                period_start=date.today(),
                period_end=date.today() + timedelta(days=30),
                categories={"groceries": CategoryBudget(limit=Decimal("500.00"))},
            )
            budget_service.create_budget(user_id, budget_data)

        # Get first page (2 items)
        page1 = budget_service.list_budgets(user_id, skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = budget_service.list_budgets(user_id, skip=2, limit=2)
        assert len(page2) == 2

        # Ensure no overlap
        assert page1[0].budget_id != page2[0].budget_id

    def test_list_budgets_isolation(self, budget_service, user_id):
        """Test that users only see their own budgets."""
        user1_id = user_id
        user2_id = uuid4()

        # Create budgets for both users
        budget_data = BudgetCreate(
            name="Test Budget",
            total_monthly=Decimal("3000.00"),
            period_start=date.today(),
            period_end=date.today() + timedelta(days=30),
            categories={"groceries": CategoryBudget(limit=Decimal("500.00"))},
        )

        budget_service.create_budget(user1_id, budget_data)
        budget_service.create_budget(user2_id, budget_data)

        user1_budgets = budget_service.list_budgets(user1_id)
        user2_budgets = budget_service.list_budgets(user2_id)

        assert len(user1_budgets) == 1
        assert len(user2_budgets) == 1
        assert user1_budgets[0].user_id != user2_budgets[0].user_id


class TestUpdateBudget:
    """Tests for updating budgets."""

    def test_update_budget_name(self, budget_service, user_id, sample_budget_data):
        """Test updating budget name."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        update = BudgetUpdate(name="February Budget")
        updated_budget = budget_service.update_budget(budget.budget_id, user_id, update)

        assert updated_budget is not None
        assert updated_budget.name == "February Budget"
        assert updated_budget.total_monthly == budget.total_monthly  # Unchanged

    def test_update_budget_total(self, budget_service, user_id, sample_budget_data):
        """Test updating total monthly amount."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        update = BudgetUpdate(total_monthly=Decimal("4000.00"))
        updated_budget = budget_service.update_budget(budget.budget_id, user_id, update)

        assert updated_budget.total_monthly == Decimal("4000.00")

    def test_update_budget_categories(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test updating budget categories."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        new_categories = {
            "groceries": CategoryBudget(
                limit=Decimal("600.00"), spent=Decimal("100.00")
            ),
            "utilities": CategoryBudget(limit=Decimal("300.00")),
        }
        update = BudgetUpdate(categories=new_categories)
        updated_budget = budget_service.update_budget(budget.budget_id, user_id, update)

        assert "utilities" in updated_budget.categories
        assert updated_budget.categories["groceries"]["limit"] == 600.0

    def test_update_budget_dates(self, budget_service, user_id, sample_budget_data):
        """Test updating budget period dates."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        new_start = date.today() + timedelta(days=30)
        new_end = date.today() + timedelta(days=60)
        update = BudgetUpdate(period_start=new_start, period_end=new_end)
        updated_budget = budget_service.update_budget(budget.budget_id, user_id, update)

        assert updated_budget.period_start == new_start
        assert updated_budget.period_end == new_end

    def test_update_budget_not_found(self, budget_service, user_id):
        """Test updating non-existent budget."""
        update = BudgetUpdate(name="New Name")
        result = budget_service.update_budget(uuid4(), user_id, update)

        assert result is None

    def test_update_budget_wrong_user(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test that user can't update another user's budget."""
        budget = budget_service.create_budget(user_id, sample_budget_data)
        different_user_id = uuid4()

        update = BudgetUpdate(name="Hacked Budget")
        result = budget_service.update_budget(
            budget.budget_id, different_user_id, update
        )

        assert result is None

    def test_update_budget_partial(self, budget_service, user_id, sample_budget_data):
        """Test partial update (only some fields)."""
        budget = budget_service.create_budget(user_id, sample_budget_data)
        original_name = budget.name

        # Only update total_monthly
        update = BudgetUpdate(total_monthly=Decimal("3500.00"))
        updated_budget = budget_service.update_budget(budget.budget_id, user_id, update)

        assert updated_budget.total_monthly == Decimal("3500.00")
        assert updated_budget.name == original_name  # Should remain unchanged


class TestDeleteBudget:
    """Tests for deleting budgets."""

    def test_delete_budget_success(self, budget_service, user_id, sample_budget_data):
        """Test successful budget deletion."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        result = budget_service.delete_budget(budget.budget_id, user_id)

        assert result is True

        # Verify it's actually deleted
        deleted_budget = budget_service.get_budget(budget.budget_id, user_id)
        assert deleted_budget is None

    def test_delete_budget_not_found(self, budget_service, user_id):
        """Test deleting non-existent budget."""
        result = budget_service.delete_budget(uuid4(), user_id)

        assert result is False

    def test_delete_budget_wrong_user(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test that user can't delete another user's budget."""
        budget = budget_service.create_budget(user_id, sample_budget_data)
        different_user_id = uuid4()

        result = budget_service.delete_budget(budget.budget_id, different_user_id)

        assert result is False

        # Verify budget still exists
        existing_budget = budget_service.get_budget(budget.budget_id, user_id)
        assert existing_budget is not None


class TestUpdateCategorySpending:
    """Tests for updating category spending."""

    def test_update_category_spending_success(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test updating spending for a category."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        updated_budget = budget_service.update_category_spending(
            budget.budget_id, user_id, "groceries", 150.00
        )

        assert updated_budget is not None
        assert updated_budget.categories["groceries"]["spent"] == 150.0

    def test_update_category_spending_multiple_times(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test updating spending multiple times (overwrite behavior)."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        # First update
        budget_service.update_category_spending(
            budget.budget_id, user_id, "groceries", 100.00
        )

        # Second update (should overwrite, not add)
        updated_budget = budget_service.update_category_spending(
            budget.budget_id, user_id, "groceries", 200.00
        )

        assert updated_budget.categories["groceries"]["spent"] == 200.0

    def test_update_category_spending_category_not_found(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test updating spending for non-existent category."""
        budget = budget_service.create_budget(user_id, sample_budget_data)

        result = budget_service.update_category_spending(
            budget.budget_id, user_id, "nonexistent", 100.00
        )

        assert result is None

    def test_update_category_spending_budget_not_found(self, budget_service, user_id):
        """Test updating spending for non-existent budget."""
        result = budget_service.update_category_spending(
            uuid4(), user_id, "groceries", 100.00
        )

        assert result is None

    def test_update_category_spending_wrong_user(
        self, budget_service, user_id, sample_budget_data
    ):
        """Test that user can't update another user's budget spending."""
        budget = budget_service.create_budget(user_id, sample_budget_data)
        different_user_id = uuid4()

        result = budget_service.update_category_spending(
            budget.budget_id, different_user_id, "groceries", 999.00
        )

        assert result is None

        # Verify spending wasn't changed
        original_budget = budget_service.get_budget(budget.budget_id, user_id)
        assert original_budget.categories["groceries"]["spent"] == 0.0
