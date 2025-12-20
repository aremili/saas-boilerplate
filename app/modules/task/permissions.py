"""
Task module permissions.

Each module registers its own permissions here.
Roles reference these permissions by codename.
"""

from app.common.auth.registry import permissions

# Task permissions
permissions.register("tasks:read", "View tasks")
permissions.register("tasks:write", "Create and edit tasks")
permissions.register("tasks:delete", "Delete tasks")
