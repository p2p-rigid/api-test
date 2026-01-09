"""
Unit of Work pattern implementation for managing database transactions.
"""
from typing import Dict, Type, Optional
from contextlib import asynccontextmanager
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base import BaseRepository
from app.repositories.user_repository import UserRepository


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing database transactions.
    Provides a way to coordinate work done by multiple repositories within a single transaction.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._repositories: Dict[Type, BaseRepository] = {}
        self.logger = structlog.get_logger(__name__).bind(uow="UnitOfWork")

    def get_repository(self, repository_cls: Type[BaseRepository]) -> BaseRepository:
        """
        Get a repository instance, creating it if it doesn't exist yet.
        
        Args:
            repository_cls: The repository class to instantiate
            
        Returns:
            An instance of the requested repository
        """
        if repository_cls not in self._repositories:
            self._repositories[repository_cls] = repository_cls(self.session)
        return self._repositories[repository_cls]

    @property
    def users(self) -> UserRepository:
        """Get the user repository."""
        return self.get_repository(UserRepository)

    @asynccontextmanager
    async def transaction(self):
        """
        Context manager for handling database transactions.
        Automatically commits on success or rolls back on failure.
        """
        self.logger.info("Starting transaction")
        try:
            yield self
            await self.commit()
            self.logger.info("Transaction committed successfully")
        except Exception as e:
            self.logger.error("Transaction failed, rolling back", error=str(e))
            await self.rollback()
            raise

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()