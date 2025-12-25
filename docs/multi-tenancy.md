# Multi-Tenancy with PostgreSQL RLS

This document explains the multi-tenancy implementation using PostgreSQL Row-Level Security (RLS).

## Overview

The SaaS boilerplate supports multi-tenancy through PostgreSQL RLS, which automatically filters data based on the current tenant context. This provides:

- **Data isolation**: Each tenant can only see their own data
- **Transparent enforcement**: Application code doesn't need explicit tenant filters
- **Database-level security**: Isolation enforced at the database layer

## Architecture

### Tenant Context Flow

```
Request → TenantContextMiddleware → JWT tenant_id → ContextVar
                                                        ↓
Database ← SET LOCAL app.current_tenant_id ← SQLAlchemy Event
```

1. **Middleware** (`app/core/middleware.py`): Extracts `tenant_id` from JWT token
2. **Context Variable** (`app/core/context.py`): Stores tenant ID for the request
3. **Database Hook** (`app/core/database.py`): Sets PostgreSQL session variable on transaction start
4. **RLS Policies**: Filter queries based on `current_setting('app.current_tenant_id')`

### Models with Tenant Scope

The following models have `tenant_id` for tenant scoping:

| Model | Isolation Type | Description |
|-------|---------------|-------------|
| `User` | Strict | Users only see their own tenant |
| `Role` | Global + Tenant | See own tenant + global roles (`tenant_id = NULL`) |
| `Permission` | Global + Tenant | See own tenant + global permissions |

### RLS Policies

**Users** (strict isolation):
```sql
CREATE POLICY tenant_isolation_users ON users
USING (tenant_id = current_setting('app.current_tenant_id', true)::int)
```

**Roles/Permissions** (tenant + global):
```sql
CREATE POLICY tenant_isolation_roles ON roles
USING (tenant_id = current_setting('app.current_tenant_id', true)::int OR tenant_id IS NULL)
```

## Usage

### User Types

| User Type | `tenant_id` | Description |
|-----------|-------------|-------------|
| **SaaS Staff** | `NULL` | Internal team (admins, support). Created by platform admin. |
| **Tenant User** | `NOT NULL` | Registered customers. Access only their tenant's data. |

### B2C Mode (Current)

In B2C mode:
- **SaaS staff** (`tenant_id = NULL`): Have global roles assigned by admin
- **Tenants** (`tenant_id != NULL`): Access only their own data, no cross-tenant visibility

```python
# Global role for SaaS staff only (tenant_id = NULL users)
Role(name="admin", description="Platform admin", tenant_id=None)

# Tenant users don't need explicit roles for basic access - 
# RLS ensures they only see their own data
```

> **Note**: Pricing-based feature access (standard, premium, etc.) will be handled by a separate subscription model (TODO).

### B2B Mode (Future)

In B2B mode, tenant admins can create tenant-specific roles and manage their users:

```python
# Tenant-specific role (only visible to tenant 1)
Role(name="billing_admin", description="Billing access", tenant_id=1)

# Tenant admin can:
# - Invite users to their tenant
# - Assign roles within their tenant
# - Manage tenant-specific permissions
```

## JWT Token Structure

The JWT token includes `tenant_id`:

```json
// SaaS Staff (tenant_id = null)
{
  "sub": "1",
  "tenant_id": null,
  "roles": ["staff"],
  "permissions": ["users:read", "users:manage"],
  "type": "access"
}

// Tenant User (tenant_id = specific tenant)
{
  "sub": "123",
  "tenant_id": 42,
  "roles": [],
  "permissions": [],
  "type": "access"
}
```

## Configuration

### Environment Variables

No additional configuration required. RLS is automatically enabled via migrations.

### Bypassing RLS

System tasks (migrations, RBAC sync) use the database superuser which bypasses RLS. The `AsyncSessionLocal` used during app startup doesn't set tenant context.

## Testing

RLS policy logic is tested in `tests/common/auth/test_rbac_rls.py`:

- Tenant isolation for roles, permissions, users
- Global role visibility
- Cross-tenant isolation

Run tests:
```bash
pytest tests/common/auth/test_rbac_rls.py -v
```

## Migration

The RLS policies are created in migration `27f0d6d11564_add_tenant_scope_to_rbac_with_rls.py`.

To apply:
```bash
alembic upgrade head
```

## Future Improvements

For B2B implementation:

1. **Tenant Admin API**: Endpoints for managing tenant-specific roles
2. **Tenant Model**: Explicit `Tenant` table for tenant metadata
3. **Invitation System**: Invite users to tenants
4. **Tenant Switching**: Allow users in multiple tenants to switch context
