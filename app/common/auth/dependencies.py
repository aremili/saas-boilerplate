"""FastAPI dependencies for authentication and authorization."""

from typing import Annotated, Callable, Optional
from fastapi import Depends, HTTPException, status, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.common.auth.models import User
from app.common.auth.repositories import UserRepository
from app.common.auth.security import decode_token

logger = get_logger(__name__)


async def get_current_user(
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    if access_token is None:
        raise credentials_exception

    payload = decode_token(access_token)
    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get(int(user_id))

    if user is None:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Dependency to get the current authenticated and active user.

    Raises:
        HTTPException: 403 if user is inactive
    """
    if not current_user.is_active:
        logger.warning(f"Inactive user attempted access: {current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_user_or_redirect(
    access_token: Annotated[Optional[str], Cookie()] = None,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency that redirects to login for anonymous users."""
    redirect = HTTPException(
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        headers={"Location": "/auth/login"},
    )

    if access_token is None:
        raise redirect

    payload = decode_token(access_token)
    if payload is None or payload.get("type") != "access":
        raise redirect

    user_id = payload.get("sub")
    if user_id is None:
        raise redirect

    user_repo = UserRepository(db)
    user = await user_repo.get(int(user_id))

    if user is None or not user.is_active:
        raise redirect

    return user


def require_role(allowed_roles: list[str]) -> Callable:
    """
    Factory for creating role-based access dependencies.

    Args:
        allowed_roles: List of role names that are allowed access

    Returns:
        Dependency function that checks user roles

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role(["admin"]))):
            ...
    """

    async def role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not any(current_user.has_role(role) for role in allowed_roles):
            logger.warning(
                f"User {current_user.id} attempted to access endpoint requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {allowed_roles}",
            )
        return current_user

    return role_checker


def require_permission(permission: str) -> Callable:
    """
    Factory for creating permission-based access dependencies.

    Args:
        permission: Permission codename required (e.g., "tasks:write")

    Returns:
        Dependency function that checks user permission

    Usage:
        @router.post("/tasks")
        async def create_task(user: User = Depends(require_permission("tasks:write"))):
            ...
    """

    async def permission_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_permission(permission):
            logger.warning(
                f"User {current_user.id} attempted to access endpoint requiring '{permission}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}",
            )
        return current_user

    return permission_checker


async def require_superuser_or_redirect(
    user: Annotated[User, Depends(get_current_user_or_redirect)],
) -> User:
    """Superuser dependency with redirect for anonymous users."""
    if not user.is_superuser:
        logger.warning(f"Non-superuser {user.id} attempted superuser access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required",
        )
    return user


# Type alias
SuperUser = Annotated[User, Depends(require_superuser_or_redirect)]
