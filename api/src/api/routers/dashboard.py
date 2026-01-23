"""Dashboard summary endpoints."""

from typing import Any, Dict, List
from uuid import UUID

from core.services.budget import BudgetService
from core.services.decision import DecisionService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard_data(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get combined dashboard data for the Command view.

    Returns:
        A dictionary containing guard score, status, trend data,
        allocation health, and recent intercepted decisions.
    """
    decision_service = DecisionService(db)
    budget_service = BudgetService(db)

    # 1. Get decision summary (guard score, status, trend, recent)
    summary = decision_service.get_dashboard_summary(user_id)

    # 2. Get active budget categories for allocation health
    # We take the most recent budget as the "active" one
    budgets = budget_service.list_budgets(user_id, limit=1)
    allocation_health = []

    if budgets:
        current_budget = budgets[0]
        # Sort categories by utilization to show highest usage first in UI
        categories = sorted(
            current_budget.categories.items(),
            key=lambda x: (float(x[1].get("spent", 0)) / float(x[1].get("limit", 1))),
            reverse=True,
        )

        for name, data in categories:
            limit = float(data.get("limit", 0))
            spent = float(data.get("spent", 0))
            percent = (spent / limit * 100) if limit > 0 else 0

            # Mapping status for UI coloring logic
            if percent < 70:
                health_status = "Healthy"
            elif percent < 95:
                health_status = "Near Capacity"
            else:
                health_status = "Over Budget"

            allocation_health.append(
                {
                    "label": name.replace("_", " ").title(),
                    "utilized": spent,
                    "limit": limit,
                    "percentage": round(percent, 1),
                    "status": health_status,
                }
            )

    return {
        "guard_score": summary["guard_score"],
        "status": summary["score_status"],
        "trend": summary["score_trend"],
        "allocation_health": allocation_health,
        "recent_intercepts": summary["recent_decisions"],
    }
