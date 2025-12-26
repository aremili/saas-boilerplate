"""
Auth module permissions.

Each module registers its own permissions here.
Roles reference these permissions by codename.
"""

from app.common.auth.registry import permissions

# User management permissions
permissions.register("users:read", "View user accounts")
permissions.register("users:manage", "Create and update users")
permissions.register("users:delete", "Delete users accounts")

# Roles permissions
permissions.register("roles:read", "View roles")
permissions.register("roles:manage", "Create and update roles")
permissions.register("roles:delete", "Delete roles")