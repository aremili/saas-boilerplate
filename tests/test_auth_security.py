"""Tests for security utilities: password hashing and JWT tokens."""

import pytest
from datetime import timedelta
from jose import jwt

from app.common.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_creates_hash(self):
        """Test that hash_password creates a bcrypt hash."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix

    def test_hash_password_unique_salts(self):
        """Test that each hash is unique due to salting."""
        password = "testpassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for incorrect password."""
        password = "testpassword123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False


class TestJWTTokens:
    """Tests for JWT token functions."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "123", "roles": ["member"]}
        token = create_access_token(data)

        assert token is not None
        assert isinstance(token, str)

        # Decode and verify
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "123"
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        data = {"sub": "123"}
        token = create_access_token(data, expires_delta=timedelta(hours=1))

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "123"

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "123"}
        token, expires_at = create_refresh_token(data)

        assert token is not None
        assert expires_at is not None

        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"

    def test_decode_token_valid(self):
        """Test decoding a valid token."""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "123"

    def test_decode_token_invalid(self):
        """Test decoding an invalid token returns None."""
        payload = decode_token("invalid.token.here")
        assert payload is None

    def test_decode_token_wrong_secret(self):
        """Test decoding with wrong secret returns None."""
        # Create token with a different secret
        token = jwt.encode(
            {"sub": "123", "type": "access"},
            "wrong-secret",
            algorithm=settings.ALGORITHM,
        )

        payload = decode_token(token)
        assert payload is None
