from typing import Generic, TypeVar, Type, Optional, List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.sql import Select

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    """Base repository with common async CRUD operations"""

    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db

    async def create(self, **kwargs) -> ModelType:
        """Create a new record"""
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelType]:
        """Get a record by ID"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalars().first()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get all records with pagination"""
        result = await self.db.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """Get a record by a specific field"""
        column = getattr(self.model, field)
        result = await self.db.execute(
            select(self.model).where(column == value)
        )
        return result.scalars().first()

    async def get_multiple_by_field(self, field: str, values: List[Any]) -> List[ModelType]:
        """Get multiple records by a specific field"""
        column = getattr(self.model, field)
        result = await self.db.execute(
            select(self.model).where(column.in_(values))
        )
        return list(result.scalars().all())

    async def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """Update a record by ID"""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.scalars().first()

    async def update_by_field(self, field: str, value: Any, **kwargs) -> List[ModelType]:
        """Update records by a specific field"""
        column = getattr(self.model, field)
        stmt = (
            update(self.model)
            .where(column == value)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return list(result.scalars().all())

    async def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def soft_delete(self, id: int, is_active_field: str = "is_active") -> bool:
        """Soft delete a record by setting is_active to False"""
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**{is_active_field: False})
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def bulk_create(self, objects_data: List[Dict[str, Any]]) -> List[ModelType]:
        """Create multiple records at once"""
        instances = [self.model(**data) for data in objects_data]
        self.db.add_all(instances)
        await self.db.flush()
        for instance in instances:
            await self.db.refresh(instance)
        return instances

    async def bulk_update(self, updates: List[Dict[str, Any]], id_field: str = "id") -> int:
        """Update multiple records at once"""
        if not updates:
            return 0

        # Extract IDs and corresponding updates
        ids = [item[id_field] for item in updates if id_field in item]
        if not ids:
            return 0

        # Build update conditions
        stmt = update(self.model).where(self.model.id.in_(ids))

        # Apply updates - this is a simplified version
        # For more complex bulk updates, consider using CASE statements
        total_updated = 0
        for update_data in updates:
            item_id = update_data.pop(id_field, None)
            if item_id is not None:
                stmt = stmt.where(self.model.id == item_id).values(**update_data)
                result = await self.db.execute(stmt)
                total_updated += result.rowcount
                await self.db.flush()

        return total_updated

    async def exists(self, **filters) -> bool:
        """Check if a record exists with given filters"""
        conditions = [getattr(self.model, k) == v for k, v in filters.items()]
        stmt = select(self.model).where(and_(*conditions)).limit(1)
        result = await self.db.execute(stmt)
        return result.first() is not None

    async def count(self, **filters) -> int:
        """Count records with optional filters"""
        if filters:
            conditions = [getattr(self.model, k) == v for k, v in filters.items()]
            stmt = select(self.model).where(and_(*conditions))
        else:
            stmt = select(self.model)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.db.execute(count_stmt)
        return result.scalar_one()

    async def filter(self, skip: int = 0, limit: int = 100, **filters) -> List[ModelType]:
        """Filter records with optional pagination"""
        conditions = [getattr(self.model, k) == v for k, v in filters.items()]
        stmt = select(self.model).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def search(self, search_fields: List[str], search_term: str,
                     skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Search records across multiple fields"""
        conditions = [
            getattr(self.model, field).ilike(f"%{search_term}%")
            for field in search_fields
        ]
        stmt = select(self.model).where(or_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())


# Import func for the count method
from sqlalchemy import func
