from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.entities.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with custom queries"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.first() is not None

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        return result.first() is not None
