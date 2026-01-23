"""Pydantic models for User."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, computed_field


class UserBase(BaseModel):
    """Base user model."""

    email: EmailStr
    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    persona_tone: Optional[str] = "balanced"
    strictness_level: Optional[int] = 5


class UserCreate(UserBase):
    """User creation model."""

    google_id: str


class UserUpdate(BaseModel):
    """User update model."""

    full_name: Optional[str] = None
    profile_picture: Optional[str] = None
    persona_tone: Optional[str] = None
    strictness_level: Optional[int] = None


class UserResponse(UserBase):
    """User response model."""

    user_id: UUID
    google_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def id(self) -> UUID:
        """Alias for user_id to match frontend expectations."""
        return self.user_id

    @computed_field
    @property
    def name(self) -> Optional[str]:
        """Alias for full_name to match frontend expectations."""
        return self.full_name

    @computed_field
    @property
    def picture(self) -> Optional[str]:
        """Alias for profile_picture to match frontend expectations."""
        return self.profile_picture

    class Config:
        from_attributes = True
