"""
Default roles configuration.
TODO: add tenant admin role

Register the default roles that should exist in the system.
These roles operate on SaaS application level.
Admins can create additional roles via the admin API.
"""

from app.common.auth.registry import roles

# Default roles

# FIXME: no need to add permissions to admin role
roles.register(
    name="admin",
    description="Administrator with user management access",
    permission_codenames=["users:read", "users:manage", "users:delete"],
)

roles.register(
    name="member",
    description="Regular member with standard access",
    permission_codenames=["users:read", "users:manage"],
)

roles.register(
    name="viewer", description="Read-only access", permission_codenames=["users:read"]
)
