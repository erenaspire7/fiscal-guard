"""Goals endpoints."""
from typing import List
from uuid import UUID

from core.models.goal import GoalCreate, GoalResponse, GoalUpdate
from core.services.goals import GoalService
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/goals", tags=["goals"])


class AddProgressRequest(BaseModel):
    """Request to add progress to a goal."""

    amount: float


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    goal_data: GoalCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new goal."""
    goal_service = GoalService(db)
    goal = goal_service.create_goal(user_id, goal_data)
    return goal


@router.get("", response_model=List[GoalResponse])
def list_goals(
    include_completed: bool = False,
    skip: int = 0,
    limit: int = 100,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all goals for the current user."""
    goal_service = GoalService(db)
    goals = goal_service.list_goals(
        user_id, include_completed=include_completed, skip=skip, limit=limit
    )
    return goals


@router.get("/{goal_id}", response_model=GoalResponse)
def get_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific goal."""
    goal_service = GoalService(db)
    goal = goal_service.get_goal(goal_id, user_id)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return goal


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a goal."""
    goal_service = GoalService(db)
    goal = goal_service.update_goal(goal_id, user_id, goal_update)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a goal."""
    goal_service = GoalService(db)
    success = goal_service.delete_goal(goal_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return None


@router.post("/{goal_id}/progress", response_model=GoalResponse)
def add_goal_progress(
    goal_id: UUID,
    progress: AddProgressRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add progress to a goal."""
    goal_service = GoalService(db)
    goal = goal_service.add_progress(goal_id, user_id, progress.amount)

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    return goal
