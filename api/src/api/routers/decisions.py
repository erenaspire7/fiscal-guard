"""API endpoints for purchase decisions."""

import base64
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from core.ai.agents.vision_agent import VisionAgent
from core.database.models import User
from core.models.cart import CartAnalysisRequest, CartAnalysisResponse, CartItem
from core.models.decision import (
    DecisionFeedback,
    PurchaseDecisionDB,
    PurchaseDecisionListResponse,
    PurchaseDecisionRequest,
    PurchaseDecisionResponse,
)
from core.observability.pii_redaction import create_trace_attributes
from core.services.decision import DecisionService
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db


class ScreenshotExtractionRequest(BaseModel):
    """Request model for screenshot-based cart extraction."""

    image_base64: str
    page_url: str
    page_type: str = "cart"


class ScreenshotExtractionResponse(BaseModel):
    """Response model for screenshot extraction."""

    items: list[CartItem]
    extraction_quality: str
    confidence_score: float
    warnings: list[str]
    validation_report: dict


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


@router.post(
    "/extract-cart-screenshot",
    response_model=ScreenshotExtractionResponse,
    status_code=status.HTTP_200_OK,
)
async def extract_cart_screenshot(
    request: ScreenshotExtractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Extract cart items from screenshot using Gemini Vision.

    This endpoint receives a screenshot from the browser extension and uses
    the VisionAgent to extract cart items securely on the backend.

    Args:
        request: Screenshot extraction request with base64 image
        db: Database session
        current_user: Authenticated user

    Returns:
        Extracted cart items with quality metrics

    Raises:
        HTTPException: If extraction fails or image is invalid
    """
    try:
        # Validate base64 image
        try:
            # Check if it's a data URL and strip prefix if present
            image_data = request.image_base64
            if image_data.startswith("data:image"):
                image_data = image_data.split(",", 1)[1]

            # Validate it's valid base64
            base64.b64decode(image_data)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid base64 image: {str(e)}",
            )

        # Create vision agent
        vision_agent = VisionAgent()

        # Build trace attributes for observability
        trace_attributes = create_trace_attributes(
            user_id=str(current_user.user_id),
            page_url=request.page_url,
            page_type=request.page_type,
            action="cart_extraction",
        )

        # Decode base64 to bytes for vision agent
        image_bytes = base64.b64decode(image_data)

        # Extract cart items using vision agent
        extraction_result = vision_agent.extract_cart_items(
            image_bytes=image_bytes, trace_attributes=trace_attributes
        )

        # Validate extraction quality
        validation_report = vision_agent.validate_extraction(extraction_result)

        # Convert extracted items to CartItem models
        cart_items = []
        from decimal import Decimal

        for item in extraction_result.items:
            cart_item = CartItem(
                item_name=item.item_name,
                price=Decimal(str(item.price)),
                quantity=item.quantity,
                urgency_badge=item.urgency_badge,
                confidence=item.confidence,
            )
            cart_items.append(cart_item)

        return ScreenshotExtractionResponse(
            items=cart_items,
            extraction_quality=extraction_result.extraction_quality,
            confidence_score=extraction_result.confidence_score,
            warnings=extraction_result.warnings,
            validation_report=validation_report,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vision extraction failed: {str(e)}",
        )


@router.post(
    "/analyze-cart",
    response_model=CartAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
)
async def analyze_cart(
    request: CartAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze cart items from browser extension.

    Processes cart items (extracted via /extract-cart-screenshot or manually provided)
    and returns individual and aggregate purchase recommendations.

    Args:
        request: Cart analysis request with extracted items
        db: Database session
        current_user: Authenticated user

    Returns:
        Individual item decisions and aggregate recommendation
    """
    service = DecisionService(db)
    return await service.analyze_cart_items(
        user_id=current_user.user_id,
        items=request.items,
        page_url=request.page_url,
        page_type=request.page_type,
    )
