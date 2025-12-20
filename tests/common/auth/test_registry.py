"""Tests for RBAC registry and sync functionality."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.registry import PermissionRegistry, RoleRegistry
from app.common.auth.rbac_sync import sync_permissions, sync_roles, sync_rbac
from app.common.auth.models import Permission, Role


class TestPermissionRegistry:
    """Tests for PermissionRegistry."""

    def test_register_permission(self):
        """Test registering a permission."""
        registry = PermissionRegistry()
        registry.register("test:read", "Test read permission")

        assert "test:read" in registry.codenames()
        perm = registry.get("test:read")
        assert perm is not None
        assert perm.codename == "test:read"
        assert perm.description == "Test read permission"

    def test_register_multiple_permissions(self):
        """Test registering multiple permissions."""
        registry = PermissionRegistry()
        registry.register("test:read", "Read")
        registry.register("test:write", "Write")
        registry.register("test:delete", "Delete")

        assert len(registry.all()) == 3
        assert registry.codenames() == {"test:read", "test:write", "test:delete"}

    def test_get_nonexistent_permission(self):
        """Test getting a permission that doesn't exist."""
        registry = PermissionRegistry()
        assert registry.get("nonexistent:permission") is None

    def test_overwrite_permission(self):
        """Test that registering same codename overwrites."""
        registry = PermissionRegistry()
        registry.register("test:read", "Old description")
        registry.register("test:read", "New description")

        assert len(registry.all()) == 1
        assert registry.get("test:read").description == "New description"


class TestRoleRegistry:
    """Tests for RoleRegistry."""

    def test_register_role(self):
        """Test registering a role."""
        registry = RoleRegistry()
        registry.register("tester", "Test role", ["test:read", "test:write"])

        role = registry.get("tester")
        assert role is not None
        assert role.name == "tester"
        assert role.description == "Test role"
        assert role.permissions == ["test:read", "test:write"]

    def test_register_role_without_permissions(self):
        """Test registering a role with no permissions."""
        registry = RoleRegistry()
        registry.register("empty_role", "Role with no permissions")

        role = registry.get("empty_role")
        assert role is not None
        assert role.permissions == []

    def test_get_nonexistent_role(self):
        """Test getting a role that doesn't exist."""
        registry = RoleRegistry()
        assert registry.get("nonexistent") is None

    def test_all_roles(self):
        """Test getting all registered roles."""
        registry = RoleRegistry()
        registry.register("role1", "Role 1")
        registry.register("role2", "Role 2")

        roles = registry.all()
        assert len(roles) == 2
        names = {r.name for r in roles}
        assert names == {"role1", "role2"}


class TestRbacSync:
    """Tests for RBAC sync functionality."""

    async def test_sync_creates_permissions(self, db_session: AsyncSession):
        """Test that sync creates permissions in database."""
        # Create a fresh registry for this test
        from app.common.auth.registry import permissions

        # Clear and add test permission
        permissions._permissions.clear()
        permissions.register("sync_test:read", "Sync test permission")

        # Sync to database
        permission_ids = await sync_permissions(db_session)
        await db_session.commit()

        # Verify permission was created
        assert "sync_test:read" in permission_ids

        # Query database directly
        from sqlalchemy import select

        result = await db_session.execute(
            select(Permission).where(Permission.codename == "sync_test:read")
        )
        perm = result.scalar_one_or_none()
        assert perm is not None
        assert perm.description == "Sync test permission"

    async def test_sync_creates_roles(self, db_session: AsyncSession):
        """Test that sync creates roles in database."""
        from app.common.auth.registry import permissions, roles

        # Clear and setup test data
        permissions._permissions.clear()
        roles._roles.clear()

        permissions.register("role_test:read", "Test permission")
        roles.register("test_role", "Test role", ["role_test:read"])

        # Sync permissions first
        permission_ids = await sync_permissions(db_session)
        await sync_roles(db_session, permission_ids)
        await db_session.commit()

        # Query database directly
        from sqlalchemy import select

        result = await db_session.execute(select(Role).where(Role.name == "test_role"))
        role = result.scalar_one_or_none()
        assert role is not None
        assert role.description == "Test role"

    async def test_sync_is_idempotent(self, db_session: AsyncSession):
        """Test that running sync multiple times doesn't duplicate data."""
        from app.common.auth.registry import permissions, roles

        # Clear and setup
        permissions._permissions.clear()
        roles._roles.clear()

        permissions.register("idempotent:test", "Test")
        roles.register("idempotent_role", "Test role", ["idempotent:test"])

        # Run sync twice
        await sync_rbac(db_session)
        await sync_rbac(db_session)

        # Should still have only one of each
        from sqlalchemy import select, func

        perm_count = await db_session.execute(
            select(func.count())
            .select_from(Permission)
            .where(Permission.codename == "idempotent:test")
        )
        assert perm_count.scalar() == 1

        role_count = await db_session.execute(
            select(func.count()).select_from(Role).where(Role.name == "idempotent_role")
        )
        assert role_count.scalar() == 1
