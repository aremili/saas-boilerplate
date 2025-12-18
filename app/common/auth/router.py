"""Authentication router with endpoints for register, login, refresh, logout, and me."""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logging import get_logger
from app.common.auth.models import User, RefreshToken
from app.common.auth.schemas import (
    UserCreate,
    UserResponse,
    Token,
    TokenRefresh,
    MessageResponse,
)
from app.common.auth.repositories import UserRepository, RefreshTokenRepository
from app.common.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.common.auth.dependencies import get_current_active_user

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters)
    """
    user_repo = UserRepository(db)
    
    # Check if email already exists
    existing_user = await user_repo.get_by_email(user_data.email)
    if existing_user:
        logger.warning(f"Registration attempt with existing email: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    user = await user_repo.create(
        email=user_data.email,
        hashed_password=hashed_pw
    )
    
    logger.info(f"New user registered: {user.email}")
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Authenticate user and return access/refresh tokens.
    
    Uses OAuth2 password flow - send credentials as form data:
    - **username**: Email address
    - **password**: Password
    """
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)
    
    # Find user by email
    user = await user_repo.get_by_email(form_data.username)
    if not user:
        logger.warning(f"Login attempt for non-existent email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Failed login attempt for user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Login attempt by inactive user: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create tokens with roles and permissions
    token_data = {
        "sub": str(user.id),
        "roles": [r.name for r in user.roles],
        "permissions": list(user.get_all_permissions()),
        "tenant_id": user.tenant_id
    }
    
    access_token = create_access_token(token_data)
    refresh_token, expires_at = create_refresh_token(token_data)
    
    # Store refresh token in database
    await token_repo.create(
        token=refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    
    logger.info(f"User logged in: {user.email}")
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """
    Get a new access token using a valid refresh token.
    
    - **refresh_token**: Valid, non-expired, non-revoked refresh token
    """
    token_repo = RefreshTokenRepository(db)
    user_repo = UserRepository(db)
    
    # Validate refresh token
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Check if token exists and is valid in database
    stored_token = await token_repo.get_valid_token(token_data.refresh_token)
    if not stored_token:
        logger.warning("Refresh token not found or revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired or revoked"
        )
    
    # Get user
    user = await user_repo.get(stored_token.user_id)
    if not user or not user.is_active:
        logger.warning(f"Token refresh for invalid/inactive user: {stored_token.user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Revoke old refresh token (token rotation)
    await token_repo.revoke_token(token_data.refresh_token)
    
    # Create new tokens with roles and permissions
    new_token_data = {
        "sub": str(user.id),
        "roles": [r.name for r in user.roles],
        "permissions": list(user.get_all_permissions()),
        "tenant_id": user.tenant_id
    }
    
    access_token = create_access_token(new_token_data)
    new_refresh_token, expires_at = create_refresh_token(new_token_data)
    
    # Store new refresh token
    await token_repo.create(
        token=new_refresh_token,
        user_id=user.id,
        expires_at=expires_at
    )
    
    logger.info(f"Tokens refreshed for user: {user.email}")
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    token_data: TokenRefresh,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> MessageResponse:
    """
    Logout by revoking the refresh token.
    
    - **refresh_token**: The refresh token to revoke
    """
    token_repo = RefreshTokenRepository(db)
    
    revoked = await token_repo.revoke_token(token_data.refresh_token)
    if revoked:
        logger.info("User logged out, refresh token revoked")
    else:
        logger.debug("Logout called with unknown/already-revoked token")
    
    return MessageResponse(message="Successfully logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
) -> User:
    """
    Get the current authenticated user's information.
    
    Requires valid access token in Authorization header.
    """
    return current_user
