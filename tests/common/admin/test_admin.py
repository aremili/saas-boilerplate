"""
Tests for Admin module endpoints.
"""

import pytest
from httpx import AsyncClient

from app.common.auth.models import User


class TestAdminPermissionsPage:
    """Tests for /admin/permissions endpoint."""

    @pytest.mark.asyncio
    async def test_permissions_page_anonymous_redirects_to_login(
        self, client: AsyncClient
    ):
        """Anonymous users are redirected to login page."""
        response = await client.get("/admin/permissions", follow_redirects=False)

        assert response.status_code == 307
        assert response.headers["location"] == "/auth/login"

    @pytest.mark.asyncio
    async def test_permissions_page_accessible_by_superuser(
        self, client: AsyncClient, superuser: User
    ):
        """Superusers can access admin permissions page."""
        login_response = await client.post(
            "/auth/login",
            data={"username": superuser.email, "password": "superpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/admin/permissions", cookies=cookies)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Registered Permissions" in response.text
        assert "Default Roles" in response.text

    @pytest.mark.asyncio
    async def test_permissions_page_shows_403_error_page(
        self, client: AsyncClient, test_user: User
    ):
        """Non-superuser sees proper 403 error page with HTML."""
        login_response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get(
            "/admin/permissions", cookies=cookies, headers={"Accept": "text/html"}
        )

        assert response.status_code == 403
        assert "text/html" in response.headers["content-type"]
        assert "Access Denied" in response.text
        assert "Superuser access required" in response.text
