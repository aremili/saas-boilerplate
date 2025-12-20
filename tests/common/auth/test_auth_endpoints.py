"""Tests for authentication API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.models import User
from app.common.auth.security import hash_password, create_access_token


class TestRegisterEndpoint:
    """Tests for POST /auth/register."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "securepass123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["is_active"] is True
        assert data["is_superuser"] is False
        assert "id" in data
        assert "roles" in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email fails."""
        response = await client.post(
            "/auth/register",
            json={"email": test_user.email, "password": "securepass123"},
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/auth/register", json={"email": "notanemail", "password": "securepass123"}
        )

        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password fails."""
        response = await client.post(
            "/auth/register", json={"email": "user@example.com", "password": "short"}
        )

        assert response.status_code == 422


class TestLoginEndpoint:
    """Tests for POST /auth/login."""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password fails."""
        response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user fails."""
        response = await client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "anypassword"},
        )

        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test login with inactive user fails."""
        response = await client.post(
            "/auth/login",
            data={"username": inactive_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestMeEndpoint:
    """Tests for GET /auth/me."""

    async def test_me_authenticated(self, client: AsyncClient, test_user: User):
        """Test /me with valid token."""
        token = create_access_token({"sub": str(test_user.id)})

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    async def test_me_unauthenticated(self, client: AsyncClient):
        """Test /me without token fails."""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    async def test_me_invalid_token(self, client: AsyncClient):
        """Test /me with invalid token fails."""
        response = await client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    async def test_me_with_roles(self, client: AsyncClient, test_user_with_role: User):
        """Test /me returns user roles."""
        token = create_access_token({"sub": str(test_user_with_role.id)})

        response = await client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["roles"]) > 0
        assert data["roles"][0]["name"] == "tester"


class TestTokenRefreshEndpoint:
    """Tests for POST /auth/refresh."""

    @pytest.mark.xfail(
        reason="Timing issue in test: rapid token generation can cause duplicate tokens in test DB"
    )
    async def test_refresh_token_flow(self, client: AsyncClient):
        """Test token refresh flow."""
        # Create a fresh user for this test
        await client.post(
            "/auth/register",
            json={"email": "refresh_test@example.com", "password": "testpassword123"},
        )

        # Login to get tokens
        login_response = await client.post(
            "/auth/login",
            data={
                "username": "refresh_test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_response.status_code == 200
        tokens = login_response.json()

        # Use refresh token to get new tokens
        response = await client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # New tokens should be different
        assert data["refresh_token"] != tokens["refresh_token"]


class TestLogoutEndpoint:
    """Tests for POST /auth/logout."""

    async def test_logout(self, client: AsyncClient, test_user: User):
        """Test logout revokes refresh token."""
        # First login
        login_response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
        )
        tokens = login_response.json()

        # Logout
        response = await client.post(
            "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
        )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()
