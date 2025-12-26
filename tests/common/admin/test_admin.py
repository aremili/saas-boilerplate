"""
Tests for Admin module endpoints.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.models import User
from app.common.auth.security import hash_password


class TestAdminPermissionsPage:
    """Tests for /admin/permissions endpoint."""

    @pytest.mark.asyncio
    async def test_permissions_page_requires_auth(self, client: AsyncClient):
        """Unauthenticated users cannot access admin page."""
        response = await client.get("/admin/permissions")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_permissions_page_requires_superuser(
        self, client: AsyncClient, test_user: User
    ):
        login_response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "testpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/admin/permissions", cookies=cookies)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_permissions_page_accessible_by_superuser(
        self, client: AsyncClient, superuser: User
    ):
        # Login as superuser via form
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
