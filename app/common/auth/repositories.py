"""Repositories for User and RefreshToken models."""
from typing import Optional, Sequence
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.repositories import BaseRepository
from app.common.auth.models import User, RefreshToken
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        logger.debug(f"Fetching user by email: {email}")
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_tenant(self, tenant_id: int) -> Sequence[User]:
        """Get all users belonging to a specific tenant."""
        logger.debug(f"Fetching users for tenant_id: {tenant_id}")
        result = await self.session.execute(
            select(User).where(User.tenant_id == tenant_id)
        )
        return result.scalars().all()
    
    async def get_active_users(self) -> Sequence[User]:
        """Get all active users."""
        logger.debug("Fetching all active users")
        result = await self.session.execute(
            select(User).where(User.is_active == True)
        )
        return result.scalars().all()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(RefreshToken, session)
    
    async def get_valid_token(self, token: str) -> Optional[RefreshToken]:
        """Get a valid (not expired, not revoked) refresh token."""
        logger.debug("Fetching valid refresh token")
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token == token,
                RefreshToken.revoked == False,
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke_token(self, token: str) -> bool:
        """Revoke a specific refresh token."""
        logger.debug("Revoking refresh token")
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == token)
            .values(revoked=True)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def revoke_all_for_user(self, user_id: int) -> int:
        """Revoke all refresh tokens for a specific user."""
        logger.info(f"Revoking all refresh tokens for user_id: {user_id}")
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
            .values(revoked=True)
        )
        await self.session.commit()
        return result.rowcount
    
    async def cleanup_expired(self) -> int:
        """Delete expired tokens (maintenance task)."""
        from sqlalchemy import delete
        logger.info("Cleaning up expired refresh tokens")
        result = await self.session.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        await self.session.commit()
        return result.rowcount
