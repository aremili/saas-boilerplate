"""Tests for authentication endpoints"""

from httpx import AsyncClient

from app.common.auth.models import User


class TestRegisterEndpoint:
    """Tests for POST /auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration redirects to login."""
        response = await client.post(
            "/auth/register",
            data={
                "email": "newuser@example.com",
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303  # Redirect
        assert response.headers["location"] == "/auth/login?registered=true"

    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with existing email shows error."""
        response = await client.post(
            "/auth/register",
            data={
                "email": test_user.email,
                "password": "securepass123",
                "password_confirm": "securepass123",
            },
        )

        assert response.status_code == 400
        assert "already registered" in response.text.lower()

    async def test_register_password_mismatch(self, client: AsyncClient):
        """Test registration with mismatched passwords shows error."""
        response = await client.post(
            "/auth/register",
            data={
                "email": "user@example.com",
                "password": "password123",
                "password_confirm": "different123",
            },
        )

        assert response.status_code == 400
        assert "do not match" in response.text.lower()

    async def test_register_short_password(self, client: AsyncClient):
        """Test registration with short password shows error."""
        response = await client.post(
            "/auth/register",
            data={
                "email": "user@example.com",
                "password": "short",
                "password_confirm": "short",
            },
        )

        assert response.status_code == 400
        assert "8 characters" in response.text.lower()


class TestLoginEndpoint:
    """Tests for POST /auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful login sets cookies and redirects."""
        response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
            follow_redirects=False,
        )

        assert response.status_code == 303  # Redirect
        assert response.headers["location"] == "/"
        # Check cookies are set
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    async def test_login_wrong_password(self, client: AsyncClient, test_user: User):
        """Test login with wrong password shows error page."""
        response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "incorrect" in response.text.lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user shows error."""
        response = await client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "anypassword"},
        )

        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, inactive_user: User):
        """Test login with inactive user shows error."""
        response = await client.post(
            "/auth/login",
            data={"username": inactive_user.email, "password": "testpassword123"},
        )

        assert response.status_code == 403
        assert "inactive" in response.text.lower()


class TestProfilePage:
    """Tests for GET /auth/me"""

    async def test_profile_authenticated_with_cookie(
        self, client: AsyncClient, test_user: User
    ):
        """Test profile page accessible with cookie auth."""
        # Login first to get cookie
        login_response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
            follow_redirects=False,
        )

        # Use cookies from login
        cookies = login_response.cookies

        response = await client.get("/auth/me", cookies=cookies)

        assert response.status_code == 200
        assert test_user.email in response.text

    async def test_profile_unauthenticated_redirects_to_login(
        self, client: AsyncClient
    ):
        """Test profile page redirects to login for anonymous users."""
        response = await client.get("/auth/me", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == "/auth/login"


class TestLogoutEndpoint:
    """Tests for POST /auth/logout."""

    async def test_logout_clears_cookies(self, client: AsyncClient, test_user: User):
        """Test logout clears cookies and redirects."""
        # First login
        login_response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        # Logout
        response = await client.post(
            "/auth/logout",
            cookies=cookies,
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/auth/login"
