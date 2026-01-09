from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
import structlog

from app.models.entities.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with custom queries"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
        self.logger = structlog.get_logger(__name__).bind(repository="UserRepository")

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        self.logger.info("Fetching user by email", email=email)
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalars().first()
        self.logger.info("User fetched by email", found=user is not None, email=email)
        return user

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        self.logger.info("Fetching user by username", username=username)
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalars().first()
        self.logger.info("User fetched by username", found=user is not None, username=username)
        return user

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        self.logger.info("Fetching active users", skip=skip, limit=limit)
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        users = list(result.scalars().all())
        self.logger.info("Active users fetched", count=len(users))
        return users

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        self.logger.info("Checking if email exists", email=email)
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        exists = result.first() is not None
        self.logger.info("Email existence checked", email=email, exists=exists)
        return exists

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        self.logger.info("Checking if username exists", username=username)
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        exists = result.first() is not None
        self.logger.info("Username existence checked", username=username, exists=exists)
        return exists
