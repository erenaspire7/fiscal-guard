"""Pydantic models for User."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None


class UserCreate(UserBase):
    """User creation model."""

    google_id: str


class UserResponse(UserBase):
    """User response model."""

    user_id: UUID
    google_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
