"""Budget endpoints."""

from typing import List, Optional
from uuid import UUID

from core.ai.budget_importer import BudgetImporter
from core.models.budget import (
    BudgetAnalysisOverTime,
    BudgetCreate,
    BudgetItemCreate,
    BudgetItemResponse,
    BudgetResponse,
    BudgetUpdate,
    BudgetWithItems,
    ChatBudgetImportRequest,
    ChatBudgetImportResponse,
)
from core.services.budget import BudgetService
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/budgets", tags=["budgets"])


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Create a new budget."""
    budget_service = BudgetService(db)
    budget = budget_service.create_budget(user_id, budget_data)
    return budget


@router.get("", response_model=List[BudgetResponse])
def list_budgets(
    skip: int = 0,
    limit: int = 100,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all budgets for the current user."""
    budget_service = BudgetService(db)
    budgets = budget_service.list_budgets(user_id, skip=skip, limit=limit)
    return budgets


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a specific budget."""
    budget_service = BudgetService(db)
    budget = budget_service.get_budget(budget_id, user_id)

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    return budget


@router.put("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: UUID,
    budget_update: BudgetUpdate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update a budget."""
    budget_service = BudgetService(db)
    budget = budget_service.update_budget(budget_id, user_id, budget_update)

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(
    budget_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete a budget."""
    budget_service = BudgetService(db)
    success = budget_service.delete_budget(budget_id, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    return None


@router.post("/import/chat", response_model=ChatBudgetImportResponse)
def chat_budget_import(
    request: ChatBudgetImportRequest,
    user_id: UUID = Depends(get_current_user_id),
):
    """Process a chat message for budget import."""
    importer = BudgetImporter()

    if not request.message:
        # Start new conversation
        return importer.start_conversation()

    response = importer.process_message(
        request.message,
        request.conversation_history,
    )

    return response


@router.get("/import/chat/start", response_model=ChatBudgetImportResponse)
def start_chat_budget_import(user_id: UUID = Depends(get_current_user_id)):
    """Start a new chat-based budget import conversation."""
    importer = BudgetImporter()
    return importer.start_conversation()


# Budget Items endpoints
@router.post(
    "/{budget_id}/items",
    response_model=BudgetItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_budget_item(
    budget_id: UUID,
    item_data: BudgetItemCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a new item to a budget and update spending."""
    budget_service = BudgetService(db)
    budget_item = budget_service.add_budget_item(budget_id, user_id, item_data)

    if not budget_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found or category does not exist in budget",
        )

    return budget_item


@router.get("/{budget_id}/items", response_model=List[BudgetItemResponse])
def get_budget_items(
    budget_id: UUID,
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get all items for a budget, optionally filtered by category."""
    budget_service = BudgetService(db)

    # Verify budget exists and belongs to user
    budget = budget_service.get_budget(budget_id, user_id)
    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    items = budget_service.get_budget_items(
        budget_id, user_id, category=category, skip=skip, limit=limit
    )
    return items


@router.get("/{budget_id}/with-items", response_model=BudgetWithItems)
def get_budget_with_items(
    budget_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get a budget with all its items."""
    budget_service = BudgetService(db)
    budget = budget_service.get_budget_with_items(budget_id, user_id)

    if not budget:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Budget not found",
        )

    # Convert to response model with items
    return BudgetWithItems(
        **budget.__dict__,
        items=[BudgetItemResponse.model_validate(item) for item in budget.budget_items],
    )


@router.get("/analysis/over-time", response_model=BudgetAnalysisOverTime)
def analyze_budgets_over_time(
    num_periods: int = Query(
        6, ge=1, le=12, description="Number of periods to analyze"
    ),
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Analyze budget performance over multiple periods.

    This provides insights into spending trends and budget adherence,
    which influence the guard score calculation.
    """
    budget_service = BudgetService(db)
    analysis = budget_service.analyze_budgets_over_time(
        user_id, num_periods=num_periods
    )
    return analysis
