"""FastAPI dependencies for authentication and authorization."""
from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.common.auth.models import User
from app.common.auth.repositories import UserRepository
from app.common.auth.security import decode_token

logger = get_logger(__name__)

# OAuth2 scheme for token extraction from Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        logger.warning("Invalid token provided")
        raise credentials_exception
    
    # Check token type
    if payload.get("type") != "access":
        logger.warning("Non-access token used for authentication")
        raise credentials_exception
    
    user_id = payload.get("sub")
    if user_id is None:
        logger.warning("Token missing 'sub' claim")
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get(int(user_id))
    
    if user is None:
        logger.warning(f"User not found for id: {user_id}")
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
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
            detail="Inactive user"
        )
    return current_user


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
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not any(current_user.has_role(role) for role in allowed_roles):
            user_roles = [r.name for r in current_user.roles]
            logger.warning(
                f"User {current_user.id} with roles {user_roles} "
                f"attempted to access endpoint requiring {allowed_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
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
        current_user: Annotated[User, Depends(get_current_active_user)]
    ) -> User:
        if not current_user.has_permission(permission):
            logger.warning(
                f"User {current_user.id} attempted to access endpoint "
                f"requiring permission '{permission}'"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    
    return permission_checker


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Dependency to require superuser access.
    
    Raises:
        HTTPException: 403 if user is not a superuser
    """
    if not current_user.is_superuser:
        logger.warning(f"Non-superuser {current_user.id} attempted superuser access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser access required"
        )
    return current_user


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
SuperUser = Annotated[User, Depends(get_current_superuser)]
