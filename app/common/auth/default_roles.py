"""
Default SaaS Staff roles configuration.

These are global roles (tenant_id = NULL) for SaaS platform staff only.
Tenant users don't use these roles - they rely on RLS for data isolation.

Staff roles:
- staff: Can manage users (read, edit) but not delete
- support: Read-only access for support/troubleshooting

Note: Platform admins use is_superuser=True on User model, no role needed.
"""

from app.common.auth.registry import roles

# Staff role - can read and manage users, but cannot delete
roles.register(
    name="staff",
    description="Staff member with user management access",
    permission_codenames=["users:read", "users:manage"],
)

# Support role - read-only access for customer support
roles.register(
    name="support",
    description="Support staff with read-only access",
    permission_codenames=["users:read"],
)
