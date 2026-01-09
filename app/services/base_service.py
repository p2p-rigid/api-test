"""
Base service class with common functionality for all services.
"""
from abc import ABC
from typing import TypeVar, Generic, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.repositories.base import BaseRepository

ModelType = TypeVar("ModelType")


class BaseService(Generic[ModelType], ABC):
    """
    Base service class with common functionality for all services.
    Provides generic CRUD operations and common utilities.
    """
    
    def __init__(self, db: AsyncSession, repository: BaseRepository[ModelType]):
        self.db = db
        self.repository = repository
        self.logger = structlog.get_logger(__name__).bind(service=self.__class__.__name__)

    async def create(self, **kwargs) -> ModelType:
        """
        Create a new record.
        
        Args:
            **kwargs: Fields to set on the new record
            
        Returns:
            The created record
        """
        self.logger.info("Creating record", **kwargs)
        instance = await self.repository.create(**kwargs)
        await self.db.commit()
        self.logger.info("Record created successfully", id=getattr(instance, 'id', 'unknown'))
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get a record by ID.
        
        Args:
            id: The ID of the record to retrieve
            
        Returns:
            The record if found, None otherwise
        """
        self.logger.info("Fetching record by ID", id=id)
        instance = await self.repository.get_by_id(id)
        self.logger.info("Record fetched", found=instance is not None, id=id)
        return instance

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of records
        """
        self.logger.info("Fetching all records", skip=skip, limit=limit)
        instances = await self.repository.get_all(skip=skip, limit=limit)
        self.logger.info("Records fetched", count=len(instances))
        return instances

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        Update a record by ID.
        
        Args:
            id: The ID of the record to update
            **kwargs: Fields to update
            
        Returns:
            The updated record if successful, None otherwise
        """
        self.logger.info("Updating record", id=id, **kwargs)
        instance = await self.repository.update(id, **kwargs)
        if instance:
            await self.db.commit()
            self.logger.info("Record updated successfully", id=id)
        else:
            self.logger.warning("Failed to update record", id=id)
        return instance

    async def delete(self, id: int) -> bool:
        """
        Delete a record by ID.
        
        Args:
            id: The ID of the record to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        self.logger.info("Deleting record", id=id)
        success = await self.repository.delete(id)
        if success:
            await self.db.commit()
            self.logger.info("Record deleted successfully", id=id)
        else:
            self.logger.warning("Failed to delete record", id=id)
        return success

    async def exists(self, **filters) -> bool:
        """
        Check if a record exists with given filters.
        
        Args:
            **filters: Filters to apply
            
        Returns:
            True if a record exists with the given filters, False otherwise
        """
        self.logger.info("Checking if record exists", **filters)
        exists = await self.repository.exists(**filters)
        self.logger.info("Existence check completed", exists=exists, **filters)
        return exists

    async def count(self, **filters) -> int:
        """
        Count records with optional filters.
        
        Args:
            **filters: Filters to apply
            
        Returns:
            Number of records matching the filters
        """
        self.logger.info("Counting records", filters=bool(filters))
        count = await self.repository.count(**filters)
        self.logger.info("Count completed", count=count, **filters)
        return count

    async def filter(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """
        Filter records with optional pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            **filters: Filters to apply
            
        Returns:
            List of records matching the filters
        """
        self.logger.info("Filtering records", skip=skip, limit=limit, **filters)
        instances = await self.repository.filter(skip=skip, limit=limit, **filters)
        self.logger.info("Filtering completed", count=len(instances), **filters)
        return instances