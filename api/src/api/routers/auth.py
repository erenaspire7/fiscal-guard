"""Authentication endpoints."""

import time
from typing import Optional

from authlib.integrations.starlette_client import OAuth
from core.config import settings
from core.models.user import UserResponse
from core.services.auth import AuthService
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, EmailStr
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


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class GoogleTokenRequest(BaseModel):
    """Google ID token exchange request."""

    id_token: str


class ExtendedTokenResponse(BaseModel):
    """Extended token response with user info."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


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
            # Redirect to frontend with error
            return RedirectResponse(
                url=f"{settings.frontend_url}/auth/error?message=Failed to get user info"
            )

        # Get or create user
        auth_service = AuthService(db)
        user = auth_service.get_or_create_user(user_data)

        # Create JWT token
        access_token = auth_service.create_access_token(str(user.user_id))

        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback?token={access_token}"
        )

    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(
            url=f"{settings.frontend_url}/auth/error?message={str(e)}"
        )


@router.post("/google/token", response_model=ExtendedTokenResponse)
async def exchange_google_token(
    token_request: GoogleTokenRequest,
    db: Session = Depends(get_db),
) -> ExtendedTokenResponse:
    """
    Exchange Google ID token for Fiscal Guard JWT.
    Used by browser extension popup OAuth flow.
    """
    try:
        # Verify token with Google
        id_info = id_token.verify_oauth2_token(
            token_request.id_token,
            google_requests.Request(),
            settings.google_client_id,
        )

        # Verify token hasn't expired
        if id_info["exp"] < time.time():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
            )

        # Verify audience matches client ID
        if id_info["aud"] != settings.google_client_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid audience"
            )

        email = id_info["email"]
        google_id = id_info["sub"]

        # Initialize auth service
        auth_service = AuthService(db)

        # Check if user exists
        user = auth_service.get_user_by_google_id(google_id)
        if not user:
            # Create new user from Google profile
            google_user_data = {
                "sub": google_id,
                "email": email,
                "name": id_info.get("name"),
                "picture": id_info.get("picture"),
            }
            user = auth_service.get_or_create_user(google_user_data)

        # Generate Fiscal Guard JWT
        access_token = auth_service.create_access_token(str(user.user_id))

        return ExtendedTokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.model_validate(user),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}"
        )


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user with email and password."""
    auth_service = AuthService(db)

    try:
        user = auth_service.create_user_with_password(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create JWT token
    access_token = auth_service.create_access_token(str(user.user_id))

    return TokenResponse(access_token=access_token)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
):
    """Login with email and password."""
    auth_service = AuthService(db)

    user = auth_service.authenticate_user(request.email, request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Create JWT token
    access_token = auth_service.create_access_token(str(user.user_id))

    return TokenResponse(access_token=access_token)


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
