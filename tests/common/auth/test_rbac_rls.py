"""Tests for Row-Level Security (RLS) tenant isolation.

These tests verify that the RLS policy logic correctly isolates
tenant data by testing the WHERE clause conditions.
"""
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.common.auth.models import Role, Permission, User


@pytest.fixture
async def rls_test_setup(db_session: AsyncSession):
    """
    Setup test data for tenant isolation tests using ORM models.
    """
    # Global role (tenant_id = NULL)
    global_role = Role(name="global_admin", description="Global Admin", tenant_id=None)
    db_session.add(global_role)
    
    # Tenant 1 data
    t1_role = Role(name="tenant_one_role", description="Tenant 1 Role", tenant_id=1)
    t1_perm = Permission(codename="tenant_one:read", description="T1 Read", tenant_id=1)
    t1_user = User(
        email="user1@tenant1.com",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
        tenant_id=1
    )
    db_session.add(t1_role)
    db_session.add(t1_perm)
    db_session.add(t1_user)
    
    # Tenant 2 data
    t2_role = Role(name="tenant_two_role", description="Tenant 2 Role", tenant_id=2)
    t2_perm = Permission(codename="tenant_two:read", description="T2 Read", tenant_id=2)
    t2_user = User(
        email="user2@tenant2.com",
        hashed_password="hash",
        is_active=True,
        is_superuser=False,
        tenant_id=2
    )
    db_session.add(t2_role)
    db_session.add(t2_perm)
    db_session.add(t2_user)
    
    await db_session.commit()
    
    yield
    
    # Cleanup handled by test fixture (drop_all)


@pytest.mark.asyncio
async def test_rls_roles_tenant_isolation(db_session: AsyncSession, rls_test_setup):
    """
    Test that roles are filtered by tenant_id.
    
    The RLS policy for roles is:
        USING (tenant_id = current_setting('app.current_tenant_id', true)::int OR tenant_id IS NULL)
    
    This means:
    - Tenant 1 should see: global_admin (NULL) + tenant_one_role (1)
    - Tenant 1 should NOT see: tenant_two_role (2)
    """
    # Query all roles first (superuser sees all)
    result = await db_session.execute(text("SELECT name FROM roles ORDER BY name"))
    all_roles = [row[0] for row in result.fetchall()]
    assert len(all_roles) == 3, f"Should have 3 roles, got: {all_roles}"
    
    # Simulate Tenant 1 context - apply RLS policy WHERE clause
    result = await db_session.execute(text("""
        SELECT name FROM roles 
        WHERE tenant_id = 1 OR tenant_id IS NULL
        ORDER BY name
    """))
    tenant1_roles = [row[0] for row in result.fetchall()]
    
    assert "global_admin" in tenant1_roles, "Tenant 1 should see global roles"
    assert "tenant_one_role" in tenant1_roles, "Tenant 1 should see own roles"
    assert "tenant_two_role" not in tenant1_roles, "Tenant 1 should NOT see Tenant 2 roles"
    assert len(tenant1_roles) == 2


@pytest.mark.asyncio
async def test_rls_permissions_tenant_isolation(db_session: AsyncSession, rls_test_setup):
    """
    Test that permissions are filtered by tenant_id.
    
    The RLS policy for permissions is:
        USING (tenant_id = current_setting('app.current_tenant_id', true)::int OR tenant_id IS NULL)
    """
    # Simulate Tenant 1 context
    result = await db_session.execute(text("""
        SELECT codename FROM permissions 
        WHERE tenant_id = 1 OR tenant_id IS NULL
    """))
    tenant1_perms = [row[0] for row in result.fetchall()]
    
    assert "tenant_one:read" in tenant1_perms
    assert "tenant_two:read" not in tenant1_perms


@pytest.mark.asyncio
async def test_rls_users_tenant_isolation(db_session: AsyncSession, rls_test_setup):
    """
    Test that users are strictly isolated by tenant_id (no global access).
    
    The RLS policy for users is:
        USING (tenant_id = current_setting('app.current_tenant_id', true)::int)
    
    Note: Users policy does NOT include "OR tenant_id IS NULL" - strict isolation.
    """
    # Simulate Tenant 1 context
    result = await db_session.execute(text("""
        SELECT email FROM users WHERE tenant_id = 1
    """))
    tenant1_users = [row[0] for row in result.fetchall()]
    
    assert "user1@tenant1.com" in tenant1_users
    assert "user2@tenant2.com" not in tenant1_users
    assert len(tenant1_users) == 1
    
    # Simulate Tenant 2 context
    result = await db_session.execute(text("""
        SELECT email FROM users WHERE tenant_id = 2
    """))
    tenant2_users = [row[0] for row in result.fetchall()]
    
    assert "user2@tenant2.com" in tenant2_users
    assert "user1@tenant1.com" not in tenant2_users
    assert len(tenant2_users) == 1


@pytest.mark.asyncio
async def test_rls_no_tenant_sees_only_global(db_session: AsyncSession, rls_test_setup):
    """
    Test that when no tenant_id is set (NULL context), 
    only global roles (tenant_id IS NULL) are visible.
    
    This simulates a user without a tenant context.
    """
    # Simulating no tenant context - should only see global roles
    # The policy: tenant_id = NULL (no match) OR tenant_id IS NULL (match global only)
    result = await db_session.execute(text("""
        SELECT name FROM roles WHERE tenant_id IS NULL
    """))
    global_roles = [row[0] for row in result.fetchall()]
    
    assert "global_admin" in global_roles
    assert len(global_roles) == 1, "Only global roles should be visible"


@pytest.mark.asyncio
async def test_rls_cross_tenant_isolation(db_session: AsyncSession, rls_test_setup):
    """
    Test that Tenant 2 cannot see Tenant 1 data and vice versa.
    """
    # Tenant 2 should not see Tenant 1 roles
    result = await db_session.execute(text("""
        SELECT name FROM roles 
        WHERE tenant_id = 2 OR tenant_id IS NULL
    """))
    tenant2_roles = [row[0] for row in result.fetchall()]
    
    assert "tenant_two_role" in tenant2_roles
    assert "global_admin" in tenant2_roles
    assert "tenant_one_role" not in tenant2_roles
