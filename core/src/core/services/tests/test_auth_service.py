"""Tests for authentication service."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings
from core.database.models import Base, User
from core.services.auth import AuthService


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture
def auth_service(db_session):
    """Create an auth service instance."""
    return AuthService(db_session)


@pytest.fixture
def sample_google_user_data():
    """Create sample Google user data."""
    return {
        "sub": "google_12345",
        "email": "testuser@example.com",
        "name": "Test User",
        "picture": "https://example.com/picture.jpg",
    }


class TestCreateAccessToken:
    """Tests for JWT token creation."""

    def test_create_access_token_success(self, auth_service):
        """Test successful token creation."""
        user_id = str(uuid4())

        token = auth_service.create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_valid_payload(self, auth_service):
        """Test that token contains correct payload."""
        user_id = str(uuid4())

        token = auth_service.create_access_token(user_id)

        # Decode token without verification (for testing)
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_expiration(self, auth_service):
        """Test that token has correct expiration time."""
        user_id = str(uuid4())

        token = auth_service.create_access_token(user_id)

        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        # Check expiration is set correctly
        exp_time = datetime.fromtimestamp(payload["exp"])
        iat_time = datetime.fromtimestamp(payload["iat"])
        time_diff = exp_time - iat_time

        # Should be approximately equal to jwt_expiration_minutes
        expected_diff = timedelta(minutes=settings.jwt_expiration_minutes)
        assert abs(time_diff - expected_diff) < timedelta(seconds=5)

    def test_create_access_token_unique_tokens(self, auth_service):
        """Test that different user IDs produce different tokens."""
        user_id_1 = str(uuid4())
        user_id_2 = str(uuid4())

        token_1 = auth_service.create_access_token(user_id_1)
        token_2 = auth_service.create_access_token(user_id_2)

        assert token_1 != token_2


class TestVerifyToken:
    """Tests for JWT token verification."""

    def test_verify_token_success(self, auth_service):
        """Test successful token verification."""
        user_id = str(uuid4())

        token = auth_service.create_access_token(user_id)
        verified_user_id = auth_service.verify_token(token)

        assert verified_user_id == user_id

    def test_verify_token_invalid_token(self, auth_service):
        """Test verification of invalid token."""
        invalid_token = "invalid.token.here"

        result = auth_service.verify_token(invalid_token)

        assert result is None

    def test_verify_token_expired_token(self, auth_service):
        """Test verification of expired token."""
        user_id = str(uuid4())

        # Create token with past expiration
        expire = datetime.utcnow() - timedelta(hours=1)
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.utcnow() - timedelta(hours=2),
        }
        expired_token = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        result = auth_service.verify_token(expired_token)

        assert result is None

    def test_verify_token_missing_subject(self, auth_service):
        """Test verification of token without subject."""
        # Create token without 'sub' claim
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"exp": expire, "iat": datetime.utcnow()}
        token = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

        result = auth_service.verify_token(token)

        assert result is None

    def test_verify_token_wrong_algorithm(self, auth_service):
        """Test verification of token signed with wrong algorithm."""
        user_id = str(uuid4())
        expire = datetime.utcnow() + timedelta(minutes=30)
        to_encode = {"sub": user_id, "exp": expire, "iat": datetime.utcnow()}

        # Sign with different algorithm
        wrong_algo_token = jwt.encode(to_encode, "wrong_secret", algorithm="HS512")

        result = auth_service.verify_token(wrong_algo_token)

        assert result is None

    def test_verify_token_tampered(self, auth_service):
        """Test verification of tampered token."""
        user_id = str(uuid4())

        token = auth_service.create_access_token(user_id)

        # Tamper with token by changing a character
        tampered_token = token[:-5] + "xxxxx"

        result = auth_service.verify_token(tampered_token)

        assert result is None


class TestGetOrCreateUser:
    """Tests for user creation from Google OAuth data."""

    def test_create_new_user(self, auth_service, sample_google_user_data):
        """Test creating a new user from Google data."""
        user = auth_service.get_or_create_user(sample_google_user_data)

        assert user is not None
        assert user.user_id is not None
        assert user.email == "testuser@example.com"
        assert user.google_id == "google_12345"
        assert user.full_name == "Test User"
        assert user.profile_picture == "https://example.com/picture.jpg"
        assert user.created_at is not None

    def test_get_existing_user_by_google_id(
        self, auth_service, sample_google_user_data
    ):
        """Test retrieving existing user by Google ID."""
        # Create user first time
        first_user = auth_service.get_or_create_user(sample_google_user_data)

        # Try to create again with same Google ID
        second_user = auth_service.get_or_create_user(sample_google_user_data)

        # Should be same user
        assert first_user.user_id == second_user.user_id
        assert first_user.email == second_user.email

    def test_get_existing_user_updates_info(
        self, auth_service, sample_google_user_data
    ):
        """Test that user info is updated on subsequent logins."""
        # Create user first time
        first_user = auth_service.get_or_create_user(sample_google_user_data)
        original_updated_at = first_user.updated_at

        # Update Google data
        updated_google_data = sample_google_user_data.copy()
        updated_google_data["name"] = "Updated Name"
        updated_google_data["picture"] = "https://example.com/new-picture.jpg"

        # Get user again with updated data
        updated_user = auth_service.get_or_create_user(updated_google_data)

        assert updated_user.user_id == first_user.user_id
        assert updated_user.full_name == "Updated Name"
        assert updated_user.profile_picture == "https://example.com/new-picture.jpg"
        assert updated_user.updated_at > original_updated_at

    def test_link_google_account_to_existing_email(
        self, auth_service, db_session, sample_google_user_data
    ):
        """Test linking Google account to existing user with same email."""
        # Create user without Google ID
        existing_user = User(
            email="testuser@example.com",
            full_name="Existing User",
        )
        db_session.add(existing_user)
        db_session.commit()

        # Try to create user with Google OAuth
        google_user = auth_service.get_or_create_user(sample_google_user_data)

        # Should be same user with Google ID added
        assert google_user.user_id == existing_user.user_id
        assert google_user.google_id == "google_12345"
        assert google_user.email == "testuser@example.com"

    def test_create_multiple_users(self, auth_service):
        """Test creating multiple different users."""
        google_data_1 = {
            "sub": "google_user_1",
            "email": "user1@example.com",
            "name": "User One",
        }
        google_data_2 = {
            "sub": "google_user_2",
            "email": "user2@example.com",
            "name": "User Two",
        }

        user_1 = auth_service.get_or_create_user(google_data_1)
        user_2 = auth_service.get_or_create_user(google_data_2)

        assert user_1.user_id != user_2.user_id
        assert user_1.email != user_2.email
        assert user_1.google_id != user_2.google_id

    def test_create_user_missing_optional_fields(self, auth_service):
        """Test creating user with minimal Google data."""
        minimal_data = {
            "sub": "google_minimal",
            "email": "minimal@example.com",
            # No name or picture
        }

        user = auth_service.get_or_create_user(minimal_data)

        assert user is not None
        assert user.email == "minimal@example.com"
        assert user.google_id == "google_minimal"
        # Optional fields should be None or default values
        assert user.full_name is None
        assert user.profile_picture is None

    def test_create_user_with_picture_url(self, auth_service):
        """Test creating user with profile picture URL."""
        google_data = {
            "sub": "google_with_pic",
            "email": "user@example.com",
            "name": "User With Picture",
            "picture": "https://lh3.googleusercontent.com/a/default-user",
        }

        user = auth_service.get_or_create_user(google_data)

        assert user.profile_picture is not None
        assert user.profile_picture.startswith("https://")


class TestGetUserById:
    """Tests for retrieving user by ID."""

    def test_get_user_by_id_success(self, auth_service, sample_google_user_data):
        """Test retrieving user by valid ID."""
        # Create user
        created_user = auth_service.get_or_create_user(sample_google_user_data)

        # Retrieve by ID
        retrieved_user = auth_service.get_user_by_id(created_user.user_id)

        assert retrieved_user is not None
        assert retrieved_user.user_id == created_user.user_id
        assert retrieved_user.email == created_user.email

    def test_get_user_by_id_not_found(self, auth_service):
        """Test retrieving user with non-existent ID."""
        non_existent_id = uuid4()

        user = auth_service.get_user_by_id(non_existent_id)

        assert user is None

    def test_get_user_by_id_returns_correct_user(
        self, auth_service, sample_google_user_data
    ):
        """Test that correct user is returned from multiple users."""
        # Create multiple users
        user_1_data = sample_google_user_data.copy()
        user_1_data["sub"] = "google_user_1"
        user_1_data["email"] = "user1@example.com"

        user_2_data = sample_google_user_data.copy()
        user_2_data["sub"] = "google_user_2"
        user_2_data["email"] = "user2@example.com"

        user_1 = auth_service.get_or_create_user(user_1_data)
        user_2 = auth_service.get_or_create_user(user_2_data)

        # Retrieve specific user
        retrieved_user = auth_service.get_user_by_id(user_1.user_id)

        assert retrieved_user.user_id == user_1.user_id
        assert retrieved_user.email == "user1@example.com"
        assert retrieved_user.user_id != user_2.user_id


class TestEndToEndAuthentication:
    """Integration tests for complete authentication flow."""

    def test_complete_auth_flow(self, auth_service, sample_google_user_data):
        """Test complete flow: create user, generate token, verify token."""
        # Step 1: User logs in with Google OAuth
        user = auth_service.get_or_create_user(sample_google_user_data)
        assert user is not None

        # Step 2: Generate JWT token
        token = auth_service.create_access_token(str(user.user_id))
        assert token is not None

        # Step 3: Verify token
        verified_user_id = auth_service.verify_token(token)
        assert verified_user_id == str(user.user_id)

        # Step 4: Retrieve user by verified ID
        from uuid import UUID

        retrieved_user = auth_service.get_user_by_id(UUID(verified_user_id))
        assert retrieved_user.user_id == user.user_id
        assert retrieved_user.email == user.email

    def test_returning_user_flow(self, auth_service, sample_google_user_data):
        """Test flow for user logging in again."""
        # First login
        first_login = auth_service.get_or_create_user(sample_google_user_data)
        first_token = auth_service.create_access_token(str(first_login.user_id))

        # Second login (returning user)
        second_login = auth_service.get_or_create_user(sample_google_user_data)
        second_token = auth_service.create_access_token(str(second_login.user_id))

        # Should be same user
        assert first_login.user_id == second_login.user_id

        # Both tokens should verify to same user
        assert auth_service.verify_token(first_token) == str(first_login.user_id)
        assert auth_service.verify_token(second_token) == str(second_login.user_id)

    def test_unauthorized_access_flow(self, auth_service):
        """Test flow with invalid token."""
        # Try to verify invalid token
        verified_user_id = auth_service.verify_token("fake.invalid.token")

        assert verified_user_id is None

        # Should not be able to get user
        if verified_user_id:
            from uuid import UUID

            user = auth_service.get_user_by_id(UUID(verified_user_id))
            assert user is None

    def test_multiple_concurrent_sessions(self, auth_service, sample_google_user_data):
        """Test user with multiple active tokens."""
        # Create user
        user = auth_service.get_or_create_user(sample_google_user_data)

        # Generate multiple tokens (simulating different devices/sessions)
        token_1 = auth_service.create_access_token(str(user.user_id))
        token_2 = auth_service.create_access_token(str(user.user_id))
        token_3 = auth_service.create_access_token(str(user.user_id))

        # All tokens should be valid
        assert auth_service.verify_token(token_1) == str(user.user_id)
        assert auth_service.verify_token(token_2) == str(user.user_id)
        assert auth_service.verify_token(token_3) == str(user.user_id)

        # Main point: all tokens work for the same user (concurrent sessions are supported)
