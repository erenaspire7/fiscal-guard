"""Goals management service."""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from core.database.models import Goal
from core.models.goal import GoalCreate, GoalResponse, GoalUpdate
from sqlalchemy.orm import Session


class GoalService:
    """Handle goal CRUD operations."""

    def __init__(self, db: Session):
        """Initialize goal service."""
        self.db = db

    def create_goal(self, user_id: UUID, goal_data: GoalCreate) -> Goal:
        """Create a new goal."""
        goal = Goal(
            user_id=user_id,
            goal_name=goal_data.goal_name,
            target_amount=goal_data.target_amount,
            current_amount=goal_data.current_amount,
            priority=goal_data.priority,
            deadline=goal_data.deadline,
        )
        self.db.add(goal)
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def get_goal(self, goal_id: UUID, user_id: UUID) -> Optional[Goal]:
        """Get a goal by ID for a specific user."""
        return (
            self.db.query(Goal)
            .filter(Goal.goal_id == goal_id, Goal.user_id == user_id)
            .first()
        )

    def list_goals(
        self,
        user_id: UUID,
        include_completed: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Goal]:
        """List all goals for a user."""
        query = self.db.query(Goal).filter(Goal.user_id == user_id)

        if not include_completed:
            query = query.filter(Goal.is_completed == False)

        return (
            query.order_by(Goal.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update_goal(
        self, goal_id: UUID, user_id: UUID, goal_update: GoalUpdate
    ) -> Optional[Goal]:
        """Update a goal."""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        update_data = goal_update.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            setattr(goal, key, value)

        # Auto-complete goal if current >= target
        if goal.current_amount >= goal.target_amount and not goal.is_completed:
            goal.is_completed = True

        goal.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(goal)
        return goal

    def delete_goal(self, goal_id: UUID, user_id: UUID) -> bool:
        """Delete a goal."""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return False

        self.db.delete(goal)
        self.db.commit()
        return True

    def add_progress(self, goal_id: UUID, user_id: UUID, amount: float) -> Optional[Goal]:
        """Add progress to a goal."""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        goal.current_amount += amount

        # Auto-complete if target reached
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True

        goal.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(goal)
        return goal
