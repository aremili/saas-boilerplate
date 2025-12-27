"""
Authentication router.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.templates import templates
from app.common.auth.models import User
from app.common.auth.repositories import UserRepository, RefreshTokenRepository
from app.common.auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.common.auth.dependencies import get_current_user_or_redirect
from app.common.auth.schemas import UserRegister

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# =============================================================================
# HTML PAGES
# =============================================================================


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse("auth/pages/login.html", {"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page."""
    return templates.TemplateResponse("auth/pages/register.html", {"request": request})


# =============================================================================
# FORM ACTIONS (POST handlers for form submissions)
# =============================================================================


@router.post("/login")
async def login(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    username: str = Form(...),
    password: str = Form(...),
):
    """
    Handle login form submission.
    """
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)

    # Validate credentials
    user = await user_repo.get_by_email(username)
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login for: {username}")
        return templates.TemplateResponse(
            "auth/pages/login.html",
            {"request": request, "error": "Incorrect email or password"},
            status_code=401,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            "auth/pages/login.html",
            {"request": request, "error": "Account is inactive"},
            status_code=403,
        )

    token_data = {
        "sub": str(user.id),
        "roles": [r.name for r in user.roles],
        "permissions": list(user.get_all_permissions()),
        "tenant_id": user.tenant_id,
    }

    access_token = create_access_token(token_data)
    refresh_token, expires_at = create_refresh_token(token_data)

    # Store refresh token
    await token_repo.create(token=refresh_token, user_id=user.id, expires_at=expires_at)
    logger.info(f"User logged in: {user.email}")

    response = RedirectResponse(url="/", status_code=303)
    cookie_settings = {
        "httponly": True,
        "secure": settings.ENVIRONMENT == "production",
        "samesite": "lax",
    }
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        **cookie_settings,  # ty:ignore[invalid-argument-type]
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        **cookie_settings,  # ty:ignore[invalid-argument-type]
    )

    return response


@router.post("/register")
async def register(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    """
    Handle registration form submission
    """
    user_repo = UserRepository(db)

    # Validate with schema
    try:
        UserRegister(email=email, password=password, password_confirm=password_confirm)
    except ValidationError as e:
        # Extract first error message
        error_msg = e.errors()[0]["msg"]
        return templates.TemplateResponse(
            "auth/pages/register.html",
            {"request": request, "error": error_msg},
            status_code=400,
        )

    # Check if email exists
    existing = await user_repo.get_by_email(email)
    if existing:
        return templates.TemplateResponse(
            "auth/pages/register.html",
            {"request": request, "error": "Email already registered"},
            status_code=400,
        )

    # Create user
    user = await user_repo.create(
        email=email,
        hashed_password=hash_password(password),
    )

    logger.info(f"New user registered: {user.email}")

    return RedirectResponse(url="/auth/login?registered=true", status_code=303)


@router.post("/logout")
async def logout(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token_repo = RefreshTokenRepository(db)

    # Revoke refresh token if present
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await token_repo.revoke_token(refresh_token)

    logger.info("User logged out")

    # Clear cookies and redirect to login
    response = RedirectResponse(url="/auth/login", status_code=303)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


# =============================================================================
# PROTECTED PAGES
# =============================================================================


@router.get("/me", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user_or_redirect)],
):
    """User profile page."""
    return templates.TemplateResponse(
        "auth/pages/profile.html", {"request": request, "user": current_user}
    )
