"""Authentication service for Google OAuth and JWT."""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from core.config import settings
from core.database.models import User
from core.models.user import UserCreate, UserResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session


class AuthService:
    """Handle authentication logic."""

    def __init__(self, db: Session):
        """Initialize auth service."""
        self.db = db

    def create_access_token(self, user_id: str) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expiration_minutes)
        to_encode = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id."""
        try:
            payload = jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
            return user_id
        except JWTError:
            return None

    def get_or_create_user(self, google_user_data: dict) -> User:
        """Get existing user or create new one from Google data."""
        google_id = google_user_data.get("sub")
        email = google_user_data.get("email")

        # Try to find existing user by google_id
        user = self.db.query(User).filter(User.google_id == google_id).first()

        if user:
            # Update user info if changed
            user.full_name = google_user_data.get("name", user.full_name)
            user.profile_picture = google_user_data.get("picture", user.profile_picture)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            return user

        # Check if user exists by email (in case they signed up differently)
        user = self.db.query(User).filter(User.email == email).first()
        if user:
            # Link google account to existing user
            user.google_id = google_id
            user.full_name = google_user_data.get("name", user.full_name)
            user.profile_picture = google_user_data.get("picture", user.profile_picture)
            user.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
            return user

        # Create new user
        new_user = User(
            email=email,
            google_id=google_id,
            full_name=google_user_data.get("name"),
            profile_picture=google_user_data.get("picture"),
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        return new_user

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.user_id == user_id).first()
