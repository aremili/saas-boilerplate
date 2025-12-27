"""Tests for auth dependencies (role and permission checks)."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.models import User, Role, Permission
from app.common.auth.security import hash_password


@pytest.fixture
async def editor_role(db_session: AsyncSession) -> Role:
    """Create an editor role with content:edit permission."""
    permission = Permission(codename="content:edit", description="Edit content")
    db_session.add(permission)

    role = Role(name="editor", description="Content editor")
    role.permissions.append(permission)
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def editor_user(db_session: AsyncSession, editor_role: Role) -> User:
    """Create a user with editor role."""
    user = User(
        email="editor@test.com",
        hashed_password=hash_password("editorpass123"),
        is_active=True,
        is_superuser=False,
    )
    user.roles.append(editor_role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user, ["roles"])
    return user


class TestRequireRole:
    """Tests for require_role dependency."""

    async def test_user_with_required_role_allowed(
        self, client: AsyncClient, editor_user: User
    ):
        """User with required role can access endpoint."""
        login_response = await client.post(
            "/auth/login",
            data={"username": editor_user.email, "password": "editorpass123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/editor-only", cookies=cookies)
        assert response.status_code == 200
        assert response.json()["email"] == editor_user.email

    async def test_user_without_required_role_forbidden(
        self, client: AsyncClient, editor_user: User
    ):
        """User without required role gets 403."""
        login_response = await client.post(
            "/auth/login",
            data={"username": editor_user.email, "password": "editorpass123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/admin-only", cookies=cookies)
        assert response.status_code == 403

    async def test_superuser_bypasses_role_check(
        self, client: AsyncClient, superuser: User
    ):
        """Superuser bypasses all role checks."""
        login_response = await client.post(
            "/auth/login",
            data={"username": superuser.email, "password": "superpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/admin-only", cookies=cookies)
        assert response.status_code == 200


class TestRequirePermission:
    """Tests for require_permission dependency."""

    async def test_user_with_permission_allowed(
        self, client: AsyncClient, editor_user: User
    ):
        """User with required permission can access."""
        login_response = await client.post(
            "/auth/login",
            data={"username": editor_user.email, "password": "editorpass123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/content-edit", cookies=cookies)
        assert response.status_code == 200
        assert response.json()["email"] == editor_user.email

    async def test_user_without_permission_forbidden(
        self, client: AsyncClient, editor_user: User
    ):
        """User without required permission gets 403."""
        login_response = await client.post(
            "/auth/login",
            data={"username": editor_user.email, "password": "editorpass123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/tasks-write", cookies=cookies)
        assert response.status_code == 403

    async def test_superuser_bypasses_permission_check(
        self, client: AsyncClient, superuser: User
    ):
        """Superuser bypasses all permission checks."""
        login_response = await client.post(
            "/auth/login",
            data={"username": superuser.email, "password": "superpassword123"},
            follow_redirects=False,
        )
        cookies = login_response.cookies

        response = await client.get("/test-deps/tasks-write", cookies=cookies)
        assert response.status_code == 200
