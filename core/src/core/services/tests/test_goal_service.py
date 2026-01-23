"""Tests for goal service."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.database.models import Base, Goal
from core.models.goal import GoalCreate, GoalUpdate
from core.services.goals import GoalService


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
def goal_service(db_session):
    """Create a goal service instance."""
    return GoalService(db_session)


@pytest.fixture
def sample_goal_data():
    """Create sample goal data."""
    return GoalCreate(
        goal_name="Emergency Fund",
        target_amount=Decimal("10000.00"),
        current_amount=Decimal("2000.00"),
        priority="high",
        deadline=date.today() + timedelta(days=365),
    )


class TestCreateGoal:
    """Tests for creating goals."""

    def test_create_goal_success(self, goal_service, user_id, sample_goal_data):
        """Test successful goal creation."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        assert goal is not None
        assert goal.goal_id is not None
        assert goal.user_id == user_id
        assert goal.goal_name == "Emergency Fund"
        assert goal.target_amount == Decimal("10000.00")
        assert goal.current_amount == Decimal("2000.00")
        assert goal.priority == "high"
        assert goal.is_completed is False
        assert goal.created_at is not None

    def test_create_goal_with_zero_current(self, goal_service, user_id):
        """Test creating goal with zero current amount."""
        goal_data = GoalCreate(
            goal_name="New Car",
            target_amount=Decimal("25000.00"),
            current_amount=Decimal("0"),
            priority="medium",
            deadline=date.today() + timedelta(days=730),
        )

        goal = goal_service.create_goal(user_id, goal_data)

        assert goal.current_amount == Decimal("0")
        assert goal.is_completed is False

    def test_create_goal_without_deadline(self, goal_service, user_id):
        """Test creating goal without deadline."""
        goal_data = GoalCreate(
            goal_name="Pay Off Debt",
            target_amount=Decimal("5000.00"),
            current_amount=Decimal("1000.00"),
            priority="high",
        )

        goal = goal_service.create_goal(user_id, goal_data)

        assert goal.deadline is None
        assert goal.goal_name == "Pay Off Debt"

    def test_create_multiple_goals(self, goal_service, user_id):
        """Test creating multiple goals for same user."""
        goal1_data = GoalCreate(
            goal_name="Vacation Fund",
            target_amount=Decimal("3000.00"),
            priority="low",
        )
        goal2_data = GoalCreate(
            goal_name="Home Down Payment",
            target_amount=Decimal("50000.00"),
            priority="high",
        )

        goal1 = goal_service.create_goal(user_id, goal1_data)
        goal2 = goal_service.create_goal(user_id, goal2_data)

        assert goal1.goal_id != goal2.goal_id
        assert goal1.goal_name == "Vacation Fund"
        assert goal2.goal_name == "Home Down Payment"

    def test_create_goal_all_priorities(self, goal_service, user_id):
        """Test creating goals with different priorities."""
        priorities = ["low", "medium", "high"]

        for priority in priorities:
            goal_data = GoalCreate(
                goal_name=f"{priority.capitalize()} Priority Goal",
                target_amount=Decimal("1000.00"),
                priority=priority,
            )
            goal = goal_service.create_goal(user_id, goal_data)

            assert goal.priority == priority


class TestGetGoal:
    """Tests for retrieving goals."""

    def test_get_goal_success(self, goal_service, user_id, sample_goal_data):
        """Test retrieving an existing goal."""
        created_goal = goal_service.create_goal(user_id, sample_goal_data)

        retrieved_goal = goal_service.get_goal(created_goal.goal_id, user_id)

        assert retrieved_goal is not None
        assert retrieved_goal.goal_id == created_goal.goal_id
        assert retrieved_goal.goal_name == created_goal.goal_name

    def test_get_goal_not_found(self, goal_service, user_id):
        """Test retrieving a non-existent goal."""
        goal = goal_service.get_goal(uuid4(), user_id)

        assert goal is None

    def test_get_goal_wrong_user(self, goal_service, user_id, sample_goal_data):
        """Test that user can't access another user's goal."""
        created_goal = goal_service.create_goal(user_id, sample_goal_data)
        different_user_id = uuid4()

        goal = goal_service.get_goal(created_goal.goal_id, different_user_id)

        assert goal is None


class TestListGoals:
    """Tests for listing goals."""

    def test_list_goals_empty(self, goal_service, user_id):
        """Test listing goals when user has none."""
        goals = goal_service.list_goals(user_id)

        assert goals == []

    def test_list_goals_multiple(self, goal_service, user_id):
        """Test listing multiple goals."""
        # Create 3 goals
        for i in range(3):
            goal_data = GoalCreate(
                goal_name=f"Goal {i + 1}",
                target_amount=Decimal("1000.00"),
                priority="medium",
            )
            goal_service.create_goal(user_id, goal_data)

        goals = goal_service.list_goals(user_id)

        assert len(goals) == 3
        # Should be ordered by most recent first
        assert goals[0].goal_name == "Goal 3"
        assert goals[2].goal_name == "Goal 1"

    def test_list_goals_exclude_completed(self, goal_service, user_id):
        """Test listing goals excludes completed by default."""
        # Create incomplete goal
        incomplete_data = GoalCreate(
            goal_name="Incomplete Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("500.00"),
            priority="medium",
        )
        goal_service.create_goal(user_id, incomplete_data)

        # Create completed goal
        completed_data = GoalCreate(
            goal_name="Completed Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            priority="medium",
        )
        completed_goal = goal_service.create_goal(user_id, completed_data)

        # Mark as completed manually
        completed_goal.is_completed = True
        goal_service.db.commit()

        # List without completed
        goals = goal_service.list_goals(user_id, include_completed=False)

        assert len(goals) == 1
        assert goals[0].goal_name == "Incomplete Goal"

    def test_list_goals_include_completed(self, goal_service, user_id):
        """Test listing goals includes completed when specified."""
        # Create incomplete goal
        incomplete_data = GoalCreate(
            goal_name="Incomplete Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("500.00"),
            priority="medium",
        )
        goal_service.create_goal(user_id, incomplete_data)

        # Create completed goal
        completed_data = GoalCreate(
            goal_name="Completed Goal",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            priority="medium",
        )
        completed_goal = goal_service.create_goal(user_id, completed_data)
        completed_goal.is_completed = True
        goal_service.db.commit()

        # List with completed
        goals = goal_service.list_goals(user_id, include_completed=True)

        assert len(goals) == 2

    def test_list_goals_pagination(self, goal_service, user_id):
        """Test pagination of goal list."""
        # Create 5 goals
        for i in range(5):
            goal_data = GoalCreate(
                goal_name=f"Goal {i + 1}",
                target_amount=Decimal("1000.00"),
                priority="medium",
            )
            goal_service.create_goal(user_id, goal_data)

        # Get first page (2 items)
        page1 = goal_service.list_goals(user_id, skip=0, limit=2)
        assert len(page1) == 2

        # Get second page
        page2 = goal_service.list_goals(user_id, skip=2, limit=2)
        assert len(page2) == 2

        # Ensure no overlap
        assert page1[0].goal_id != page2[0].goal_id

    def test_list_goals_isolation(self, goal_service, user_id):
        """Test that users only see their own goals."""
        user1_id = user_id
        user2_id = uuid4()

        # Create goals for both users
        goal_data = GoalCreate(
            goal_name="Test Goal",
            target_amount=Decimal("1000.00"),
            priority="medium",
        )

        goal_service.create_goal(user1_id, goal_data)
        goal_service.create_goal(user2_id, goal_data)

        user1_goals = goal_service.list_goals(user1_id)
        user2_goals = goal_service.list_goals(user2_id)

        assert len(user1_goals) == 1
        assert len(user2_goals) == 1
        assert user1_goals[0].user_id != user2_goals[0].user_id


class TestUpdateGoal:
    """Tests for updating goals."""

    def test_update_goal_name(self, goal_service, user_id, sample_goal_data):
        """Test updating goal name."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        update = GoalUpdate(goal_name="Updated Emergency Fund")
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal is not None
        assert updated_goal.goal_name == "Updated Emergency Fund"
        assert updated_goal.target_amount == goal.target_amount  # Unchanged

    def test_update_goal_target_amount(self, goal_service, user_id, sample_goal_data):
        """Test updating target amount."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        update = GoalUpdate(target_amount=Decimal("15000.00"))
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.target_amount == Decimal("15000.00")

    def test_update_goal_current_amount(self, goal_service, user_id, sample_goal_data):
        """Test updating current amount."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        update = GoalUpdate(current_amount=Decimal("5000.00"))
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.current_amount == Decimal("5000.00")
        assert updated_goal.is_completed is False  # Not reached target yet

    def test_update_goal_auto_complete(self, goal_service, user_id, sample_goal_data):
        """Test that goal auto-completes when current >= target."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        # Update current to meet target
        update = GoalUpdate(current_amount=Decimal("10000.00"))
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.current_amount == Decimal("10000.00")
        assert updated_goal.is_completed is True

    def test_update_goal_auto_complete_exceed_target(
        self, goal_service, user_id, sample_goal_data
    ):
        """Test that goal auto-completes when current > target."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        # Update current to exceed target
        update = GoalUpdate(current_amount=Decimal("12000.00"))
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.current_amount == Decimal("12000.00")
        assert updated_goal.is_completed is True

    def test_update_goal_priority(self, goal_service, user_id, sample_goal_data):
        """Test updating priority."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        update = GoalUpdate(priority="low")
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.priority == "low"

    def test_update_goal_deadline(self, goal_service, user_id, sample_goal_data):
        """Test updating deadline."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        new_deadline = date.today() + timedelta(days=730)
        update = GoalUpdate(deadline=new_deadline)
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.deadline == new_deadline

    def test_update_goal_not_found(self, goal_service, user_id):
        """Test updating non-existent goal."""
        update = GoalUpdate(goal_name="New Name")
        result = goal_service.update_goal(uuid4(), user_id, update)

        assert result is None

    def test_update_goal_wrong_user(self, goal_service, user_id, sample_goal_data):
        """Test that user can't update another user's goal."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        different_user_id = uuid4()

        update = GoalUpdate(goal_name="Hacked Goal")
        result = goal_service.update_goal(goal.goal_id, different_user_id, update)

        assert result is None

    def test_update_goal_partial(self, goal_service, user_id, sample_goal_data):
        """Test partial update (only some fields)."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        original_name = goal.goal_name

        # Only update current_amount
        update = GoalUpdate(current_amount=Decimal("3000.00"))
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.current_amount == Decimal("3000.00")
        assert updated_goal.goal_name == original_name  # Should remain unchanged

    def test_update_goal_completion_flag(self, goal_service, user_id, sample_goal_data):
        """Test manually marking goal as completed."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        update = GoalUpdate(is_completed=True)
        updated_goal = goal_service.update_goal(goal.goal_id, user_id, update)

        assert updated_goal.is_completed is True


class TestDeleteGoal:
    """Tests for deleting goals."""

    def test_delete_goal_success(self, goal_service, user_id, sample_goal_data):
        """Test successful goal deletion."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        result = goal_service.delete_goal(goal.goal_id, user_id)

        assert result is True

        # Verify it's actually deleted
        deleted_goal = goal_service.get_goal(goal.goal_id, user_id)
        assert deleted_goal is None

    def test_delete_goal_not_found(self, goal_service, user_id):
        """Test deleting non-existent goal."""
        result = goal_service.delete_goal(uuid4(), user_id)

        assert result is False

    def test_delete_goal_wrong_user(self, goal_service, user_id, sample_goal_data):
        """Test that user can't delete another user's goal."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        different_user_id = uuid4()

        result = goal_service.delete_goal(goal.goal_id, different_user_id)

        assert result is False

        # Verify goal still exists
        existing_goal = goal_service.get_goal(goal.goal_id, user_id)
        assert existing_goal is not None


class TestAddProgress:
    """Tests for adding progress to goals."""

    def test_add_progress_success(self, goal_service, user_id, sample_goal_data):
        """Test adding progress to a goal."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        original_amount = goal.current_amount

        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 500.00)

        assert updated_goal is not None
        assert updated_goal.current_amount == original_amount + Decimal("500.00")
        assert updated_goal.is_completed is False

    def test_add_progress_reaches_target(self, goal_service, user_id, sample_goal_data):
        """Test that goal completes when progress reaches target."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        # Add progress to reach target (current: 2000, need 8000 more to reach 10000)
        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 8000.00)

        assert updated_goal.current_amount == Decimal("10000.00")
        assert updated_goal.is_completed is True

    def test_add_progress_exceeds_target(self, goal_service, user_id, sample_goal_data):
        """Test that goal completes when progress exceeds target."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        # Add more than needed
        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 10000.00)

        assert updated_goal.current_amount == Decimal("12000.00")
        assert updated_goal.is_completed is True

    def test_add_progress_multiple_times(self, goal_service, user_id, sample_goal_data):
        """Test adding progress multiple times."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        # Add progress three times
        goal = goal_service.add_progress(goal.goal_id, user_id, 500.00)
        goal = goal_service.add_progress(goal.goal_id, user_id, 1000.00)
        goal = goal_service.add_progress(goal.goal_id, user_id, 250.00)

        # Original: 2000, added: 1750, total: 3750
        assert goal.current_amount == Decimal("3750.00")
        assert goal.is_completed is False

    def test_add_progress_small_amounts(self, goal_service, user_id, sample_goal_data):
        """Test adding small progress amounts."""
        goal = goal_service.create_goal(user_id, sample_goal_data)

        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 10.50)

        assert updated_goal.current_amount == Decimal("2010.50")

    def test_add_progress_goal_not_found(self, goal_service, user_id):
        """Test adding progress to non-existent goal."""
        result = goal_service.add_progress(uuid4(), user_id, 100.00)

        assert result is None

    def test_add_progress_wrong_user(self, goal_service, user_id, sample_goal_data):
        """Test that user can't add progress to another user's goal."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        different_user_id = uuid4()

        result = goal_service.add_progress(goal.goal_id, different_user_id, 500.00)

        assert result is None

        # Verify progress wasn't added
        original_goal = goal_service.get_goal(goal.goal_id, user_id)
        assert original_goal.current_amount == Decimal("2000.00")

    def test_add_progress_zero_amount(self, goal_service, user_id, sample_goal_data):
        """Test adding zero progress (no-op but should succeed)."""
        goal = goal_service.create_goal(user_id, sample_goal_data)
        original_amount = goal.current_amount

        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 0.00)

        assert updated_goal.current_amount == original_amount

    def test_add_progress_to_completed_goal(self, goal_service, user_id):
        """Test adding progress to already completed goal."""
        # Create completed goal
        goal_data = GoalCreate(
            goal_name="Already Done",
            target_amount=Decimal("1000.00"),
            current_amount=Decimal("1000.00"),
            priority="medium",
        )
        goal = goal_service.create_goal(user_id, goal_data)

        # Manually mark as completed
        goal.is_completed = True
        goal_service.db.commit()

        # Add more progress
        updated_goal = goal_service.add_progress(goal.goal_id, user_id, 500.00)

        # Progress should still be added
        assert updated_goal.current_amount == Decimal("1500.00")
        assert updated_goal.is_completed is True
