"""Internal API endpoints for testing and evaluation.

SECURITY: These endpoints should only be accessible in development/testing environments.
Production deployments must set ALLOW_INTERNAL_ENDPOINTS=false in environment.
"""

from typing import Optional

from core.config import settings
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/internal", tags=["internal"])

# In-memory storage for prompt overrides
# In production, this could be Redis for multi-instance deployments
_prompt_overrides: dict[str, dict] = {}


class PromptOverride(BaseModel):
    """Prompt override configuration for testing."""

    agent_type: str  # "decision_agent" or "intent_classifier"
    prompt: str  # Full prompt text
    session_id: str  # Unique identifier for this override


@router.post("/set-prompt", status_code=status.HTTP_200_OK)
def set_prompt_override(
    override: PromptOverride,
    x_internal_token: Optional[str] = Header(None),
) -> dict:
    """Set a prompt override for testing different prompt versions.

    This endpoint allows evaluation scripts to inject custom prompts into agents
    for A/B testing and prompt optimization.

    Args:
        override: Prompt override configuration
        x_internal_token: Internal API token (required)

    Returns:
        Confirmation with session_id

    Raises:
        HTTPException 403: If internal endpoints are disabled
        HTTPException 401: If token is invalid
    """
    # Check if internal endpoints are enabled
    if not settings.allow_internal_endpoints:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal endpoints are disabled in this environment",
        )

    # Validate token
    if not x_internal_token or x_internal_token != settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API token",
        )

    # Store override
    _prompt_overrides[override.session_id] = {
        "agent_type": override.agent_type,
        "prompt": override.prompt,
    }

    return {
        "status": "ok",
        "session_id": override.session_id,
        "agent_type": override.agent_type,
    }


@router.delete("/clear-prompt/{session_id}", status_code=status.HTTP_200_OK)
def clear_prompt_override(
    session_id: str,
    x_internal_token: Optional[str] = Header(None),
) -> dict:
    """Clear a prompt override.

    Args:
        session_id: Session ID to clear
        x_internal_token: Internal API token (required)

    Returns:
        Confirmation

    Raises:
        HTTPException 403: If internal endpoints are disabled
        HTTPException 401: If token is invalid
        HTTPException 404: If session not found
    """
    # Check if internal endpoints are enabled
    if not settings.allow_internal_endpoints:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Internal endpoints are disabled in this environment",
        )

    # Validate token
    if not x_internal_token or x_internal_token != settings.internal_api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API token",
        )

    # Clear override
    if session_id not in _prompt_overrides:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No prompt override found for session: {session_id}",
        )

    del _prompt_overrides[session_id]

    return {"status": "ok", "session_id": session_id}


def get_prompt_override(session_id: str, agent_type: str) -> Optional[str]:
    """Get a prompt override if it exists.

    This is a helper function called by agents to check for overrides.

    Args:
        session_id: Session ID to check
        agent_type: Type of agent (decision_agent, intent_classifier)

    Returns:
        Override prompt text if found, None otherwise
    """
    if not session_id:
        return None

    override = _prompt_overrides.get(session_id)
    if override and override["agent_type"] == agent_type:
        return override["prompt"]

    return None
