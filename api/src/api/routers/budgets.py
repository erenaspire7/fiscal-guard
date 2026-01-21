"""Budget endpoints."""
from typing import List
from uuid import UUID

from core.ai.budget_importer import BudgetImporter
from core.models.budget import (
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
    ChatBudgetImportRequest,
    ChatBudgetImportResponse,
)
from core.services.budget import BudgetService
from fastapi import APIRouter, Depends, HTTPException, status
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
