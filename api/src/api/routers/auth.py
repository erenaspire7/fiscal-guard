"""Authentication endpoints."""
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from core.config import settings
from core.models.user import UserResponse
from core.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_current_user_id, get_db

router = APIRouter(prefix="/auth", tags=["auth"])

# OAuth setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.google_client_id,
    client_secret=settings.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


class TokenResponse(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth login page."""
    redirect_uri = settings.google_redirect_uri
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback."""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_data = token.get("userinfo")

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google",
            )

        # Get or create user
        auth_service = AuthService(db)
        user = auth_service.get_or_create_user(user_data)

        # Create JWT token
        access_token = auth_service.create_access_token(str(user.user_id))

        # In production, redirect to frontend with token
        # For now, return the token
        return TokenResponse(access_token=access_token)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}",
        )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get current authenticated user."""
    auth_service = AuthService(db)
    user = auth_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
