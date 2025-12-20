"""
RBAC Sync Service - Syncs registered permissions and roles to the database.

Called on app startup to ensure all declared permissions and roles exist.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.auth.models import Role, Permission, role_permissions
from app.common.auth.registry import (
    permissions as permission_registry,
    roles as role_registry,
)
from app.core.logging import get_logger


logger = get_logger(__name__)


async def sync_permissions(session: AsyncSession) -> dict[str, int]:
    """
    Sync all registered permissions to the database.

    Creates any permissions that don't exist yet.
    Returns a mapping of codename -> permission_id for role assignment.
    """
    permission_ids: dict[str, int] = {}

    for perm_def in permission_registry.all():
        # Check if permission exists
        result = await session.execute(
            select(Permission).where(Permission.codename == perm_def.codename)
        )
        permission = result.scalar_one_or_none()

        if not permission:
            # permission doesn't exist, create it
            permission = Permission(
                codename=perm_def.codename, description=perm_def.description
            )
            session.add(permission)
            await session.flush()
            logger.info(f"Created permission: {perm_def.codename}")
        else:
            # Update description if needed
            if permission.description != perm_def.description:
                permission.description = perm_def.description
                logger.debug(f"Updated permission description: {perm_def.codename}")

        permission_ids[perm_def.codename] = permission.id

    return permission_ids


async def sync_roles(session: AsyncSession, permission_ids: dict[str, int]) -> None:
    """
    Sync all registered default roles to the database.

    Creates roles that don't exist and ensures they have their declared permissions.

    Args:
        session (AsyncSession): Database session
        permission_ids (dict[str, int]): Mapping of permission codename -> permission_id
    """
    for role_def in role_registry.all():
        # Check if role exists
        result = await session.execute(select(Role).where(Role.name == role_def.name))
        role = result.scalar_one_or_none()

        if not role:
            # role doesn't exist, create it
            role = Role(name=role_def.name, description=role_def.description)
            session.add(role)
            await session.flush()
            logger.info(f"Created role: {role_def.name}")
        else:
            # Update description if changed
            if role.description != role_def.description:
                role.description = role_def.description

        # Get existing permission IDs for this role
        existing_result = await session.execute(
            select(role_permissions.c.permission_id).where(
                role_permissions.c.role_id == role.id
            )
        )
        existing_perm_ids = {row[0] for row in existing_result.fetchall()}

        # Add any missing permissions in intermediate table
        for perm_codename in role_def.permissions:
            if perm_codename in permission_ids:
                perm_id = permission_ids[perm_codename]
                if perm_id not in existing_perm_ids:
                    await session.execute(
                        role_permissions.insert().values(
                            role_id=role.id, permission_id=perm_id
                        )
                    )
                    logger.info(f"Assigned {perm_codename} to role {role_def.name}")


async def sync_rbac(session: AsyncSession) -> None:
    """
    Main sync function - call this on app startup.

    Syncs all registered permissions and roles to the database.
    """
    logger.info("Syncing RBAC permissions and roles...")

    permission_ids = await sync_permissions(session)
    await sync_roles(session, permission_ids)
    await session.commit()

    logger.info(
        f"RBAC sync complete: {len(permission_ids)} permissions, {len(role_registry.all())} roles"
    )
