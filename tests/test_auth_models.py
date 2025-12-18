"""Tests for RBAC models: Role, Permission, User relationships."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.models import User, Role, Permission, CODENAME_PATTERN


class TestPermissionModel:
    """Tests for Permission model."""

    def test_codename_pattern_valid(self):
        """Test valid codename patterns."""
        valid_patterns = [
            "tasks:read",
            "tasks:write",
            "users:manage",
            "some_resource:some_action",
        ]
        for pattern in valid_patterns:
            assert CODENAME_PATTERN.match(pattern), (
                f"Pattern should be valid: {pattern}"
            )

    def test_codename_pattern_invalid(self):
        """Test invalid codename patterns."""
        invalid_patterns = [
            "tasks",  # Missing action
            "tasksread",  # Missing colon
            "Tasks:read",  # Uppercase
            "tasks:Read",  # Uppercase action
            "tasks:read:extra",  # Too many colons
            "tasks:",  # Missing action
            ":read",  # Missing resource
            "",  # Empty
        ]
        for pattern in invalid_patterns:
            assert not CODENAME_PATTERN.match(pattern), (
                f"Pattern should be invalid: {pattern}"
            )

    async def test_create_permission(self, db_session: AsyncSession):
        """Test creating a permission."""
        permission = Permission(codename="test:create", description="Test create")
        db_session.add(permission)
        await db_session.commit()

        assert permission.id is not None
        assert permission.codename == "test:create"
        assert permission.description == "Test create"

    async def test_permission_codename_validation(self, db_session: AsyncSession):
        """Test that invalid codenames raise ValueError."""
        with pytest.raises(ValueError, match="Invalid codename"):
            Permission(codename="InvalidCodename", description="Should fail")


class TestRoleModel:
    """Tests for Role model."""

    async def test_create_role(self, db_session: AsyncSession):
        """Test creating a role."""
        role = Role(name="test_role", description="Test role")
        db_session.add(role)
        await db_session.commit()

        assert role.id is not None
        assert role.name == "test_role"

    async def test_role_with_permissions(self, db_session: AsyncSession):
        """Test role with permissions relationship."""
        permission = Permission(codename="test:action", description="Test")
        role = Role(name="test_role", description="Test role")
        role.permissions.append(permission)

        db_session.add(role)
        await db_session.commit()

        assert len(role.permissions) == 1
        assert role.permissions[0].codename == "test:action"


class TestUserModel:
    """Tests for User model and RBAC methods."""

    async def test_create_user(self, db_session: AsyncSession):
        """Test creating a user."""
        user = User(
            email="newuser@example.com",
            hashed_password="hashedpassword",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

        assert user.id is not None
        assert user.email == "newuser@example.com"
        assert user.is_active is True
        assert user.is_superuser is False

    async def test_has_role_without_roles(self, test_user: User):
        """Test has_role returns False when user has no roles."""
        assert test_user.has_role("admin") is False
        assert test_user.has_role("member") is False

    async def test_has_role_with_role(self, test_user_with_role: User):
        """Test has_role returns True when user has the role."""
        assert test_user_with_role.has_role("tester") is True
        assert test_user_with_role.has_role("other_role") is False

    async def test_has_permission_without_roles(self, test_user: User):
        """Test has_permission returns False when user has no roles."""
        assert test_user.has_permission("tests:read") is False

    async def test_has_permission_with_role(self, test_user_with_role: User):
        """Test has_permission returns True when user has permission via role."""
        assert test_user_with_role.has_permission("tests:read") is True
        assert test_user_with_role.has_permission("other:permission") is False

    async def test_superuser_has_all_permissions(self, superuser: User):
        """Test superuser bypasses all permission checks."""
        assert superuser.has_permission("any:permission") is True
        assert superuser.has_permission("nonexistent:action") is True

    async def test_get_all_permissions(self, test_user_with_role: User):
        """Test get_all_permissions returns all permission codenames."""
        permissions = test_user_with_role.get_all_permissions()
        assert "tests:read" in permissions

    async def test_get_all_permissions_empty(self, test_user: User):
        """Test get_all_permissions returns empty set for user without roles."""
        permissions = test_user.get_all_permissions()
        assert len(permissions) == 0
