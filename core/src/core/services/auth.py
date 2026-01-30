"""Authentication service for Google OAuth and JWT."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from core.config import settings
from core.database.models import User


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
            user_id = payload.get("sub")

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

    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        return self.db.query(User).filter(User.google_id == google_id).first()

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        # Ensure password is truncated to 72 bytes for bcrypt
        password_bytes = password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash."""
        password_bytes = plain_password.encode("utf-8")
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]

        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))

    def create_user_with_password(
        self, email: str, password: str, full_name: Optional[str] = None
    ) -> User:
        """Create a new user with email and password."""
        # Check if user already exists
        existing = self.db.query(User).filter(User.email == email).first()
        if existing:
            raise ValueError("User with this email already exists")

        # Validate password length (bcrypt has 72 byte limit)
        if len(password.encode("utf-8")) > 72:
            raise ValueError("Password cannot be longer than 72 bytes")

        # Create new user
        user = User(
            email=email,
            password_hash=self.hash_password(password),
            full_name=full_name,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.db.query(User).filter(User.email == email).first()
        if not user or not user.password_hash:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
