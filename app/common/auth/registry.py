"""
Permission and Role Registry for RBAC.

Modules register permissions and roles to the database on startup.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class PermissionDef:
    """Permission definition."""

    codename: str
    description: str


@dataclass
class RoleDef:
    """Role definition with its permissions."""

    name: str
    description: str
    permissions: list[str] = field(default_factory=list)


class PermissionRegistry:
    """
    Central registry for permissions.

    Modules register their permissions by calling register().
    On app startup, sync_to_db() creates any missing permissions.

    Usage:
        # In app/modules/billing/permissions.py
        from app.common.auth.registry import permissions

        permissions.register("billing:view", "View invoices")
        permissions.register("billing:manage", "Create and edit invoices")
    """

    def __init__(self):
        self._permissions: dict[str, PermissionDef] = {}

    def register(self, codename: str, description: str) -> None:
        """Register a permission."""
        self._permissions[codename] = PermissionDef(
            codename=codename, description=description
        )

    def all(self) -> list[PermissionDef]:
        """Get all registered permissions."""
        return list(self._permissions.values())

    def get(self, codename: str) -> Optional[PermissionDef]:
        """Get a permission by codename."""
        return self._permissions.get(codename)

    def codenames(self) -> set[str]:
        """Get all registered permission codenames."""
        return set(self._permissions.keys())


class RoleRegistry:
    """
    Central registry for default roles.

    These are roles that should exist by default (admin, member, viewer).
    Additional roles can be created via admin API.

    Usage:
        from app.common.auth.registry import roles

        roles.register("billing_admin", "Full billing access", ["billing:view", "billing:manage"])
    """

    def __init__(self):
        self._roles: dict[str, RoleDef] = {}

    def register(
        self,
        name: str,
        description: str,
        permission_codenames: Optional[list[str]] = None,
    ) -> None:
        """Register a default role."""
        if permission_codenames is None:
            permission_codenames: list[str] = []
        self._roles[name] = RoleDef(
            name=name, description=description, permissions=permission_codenames
        )

    def all(self) -> list[RoleDef]:
        """Get all registered roles."""
        return list(self._roles.values())

    def get(self, name: str) -> Optional[RoleDef]:
        """Get a role by name."""
        return self._roles.get(name)


# Global registry instances - modules import and use these
permissions = PermissionRegistry()
roles = RoleRegistry()
