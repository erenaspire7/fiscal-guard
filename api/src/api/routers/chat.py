"""API endpoints for conversational chat interface."""

import json

from core.database.models import User
from core.models.conversation import ConversationRequest, ConversationResponse
from core.services.conversation import ConversationService
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post(
    "/message", response_model=ConversationResponse, status_code=status.HTTP_200_OK
)
def send_message(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Process a conversational message.

    This endpoint handles all types of conversational messages:
    - Purchase decisions ("Should I buy X?")
    - Purchase feedback ("I bought it", "I didn't buy it")
    - Budget queries ("How much do I have left for groceries?")
    - Goal updates ("Add $500 to emergency fund")
    - General questions ("Am I doing well financially?")

    The message is automatically classified and routed to the appropriate handler
    using the graph-based multi-agent architecture.

    Args:
        request: Conversation request with message and history
        db: Database session
        current_user: Authenticated user

    Returns:
        Conversation response with appropriate action taken
    """
    service = ConversationService(db)
    return service.handle_message(current_user.user_id, request)


@router.post("/stream")
async def stream_message(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Stream a conversational message response.

    Uses the graph-based multi-agent architecture with streaming support.

    Returns:
        NDJSON stream of response chunks
    """
    service = ConversationService(db)

    async def generate():
        async for chunk in service.stream_handle_message(current_user.user_id, request):
            yield json.dumps(chunk) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")
