"""
Dependency container module for managing service dependencies.
This module provides factory functions for creating services with proper dependency injection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.core.uow import UnitOfWork
from fastapi import Depends


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """
    Factory function to create a UserService instance with dependency injection.

    Args:
        db: Database session (injected via FastAPI dependency system)

    Returns:
        UserService instance with injected database session
    """
    return UserService(db)


async def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    """
    Factory function to create a UserRepository instance with dependency injection.

    Args:
        db: Database session (injected via FastAPI dependency system)

    Returns:
        UserRepository instance with injected database session
    """
    return UserRepository(db)


async def get_unit_of_work(db: AsyncSession = Depends(get_db)) -> UnitOfWork:
    """
    Factory function to create a UnitOfWork instance with dependency injection.

    Args:
        db: Database session (injected via FastAPI dependency system)

    Returns:
        UnitOfWork instance with injected database session
    """
    return UnitOfWork(db)