"""API endpoints for purchase decisions."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from core.database.models import User
from core.models.decision import (
    DecisionFeedback,
    PurchaseDecisionDB,
    PurchaseDecisionListResponse,
    PurchaseDecisionRequest,
    PurchaseDecisionResponse,
)
from core.services.decision import DecisionService
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db

router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post(
    "", response_model=PurchaseDecisionResponse, status_code=status.HTTP_201_CREATED
)
def create_decision(
    request: PurchaseDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new purchase decision.

    Analyzes the purchase request using AI and returns a recommendation.

    Args:
        request: Purchase decision request
        db: Database session
        current_user: Authenticated user

    Returns:
        Purchase decision with score and reasoning
    """
    service = DecisionService(db)
    return service.create_decision(current_user.user_id, request)


@router.get("", response_model=PurchaseDecisionListResponse)
def list_decisions(
    limit: int = 50,
    offset: int = 0,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List user's purchase decisions.

    Args:
        limit: Maximum number of decisions to return
        offset: Number of decisions to skip
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of purchase decisions
    """
    service = DecisionService(db)
    return service.list_decisions(
        current_user.user_id,
        limit,
        offset,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/stats")
def get_decision_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get decision statistics for the user.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        Decision statistics
    """
    service = DecisionService(db)
    return service.get_decision_stats(current_user.user_id)


@router.get("/{decision_id}", response_model=PurchaseDecisionDB)
def get_decision(
    decision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific decision.

    Args:
        decision_id: Decision ID
        db: Database session
        current_user: Authenticated user

    Returns:
        Purchase decision

    Raises:
        HTTPException: If decision not found
    """
    service = DecisionService(db)
    decision = service.get_decision(current_user.user_id, decision_id)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found"
        )

    return decision


@router.post("/{decision_id}/feedback", response_model=PurchaseDecisionDB)
def add_decision_feedback(
    decision_id: UUID,
    feedback: DecisionFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add feedback to a decision.

    Allows users to report whether they actually made the purchase
    and how they feel about the decision.

    Args:
        decision_id: Decision ID
        feedback: User feedback
        db: Database session
        current_user: Authenticated user

    Returns:
        Updated decision

    Raises:
        HTTPException: If decision not found
    """
    service = DecisionService(db)
    decision = service.add_feedback(current_user.user_id, decision_id, feedback)

    if not decision:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Decision not found"
        )

    return decision
