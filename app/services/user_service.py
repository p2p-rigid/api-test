from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.entities.user import User
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
)


class UserService:
    """Service layer for user business logic"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = UserRepository(db)

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """Create a new user"""
        # Check if email already exists
        if await self.repository.email_exists(email):
            raise UserAlreadyExistsException("email", email)

        # Check if username already exists
        if await self.repository.username_exists(username):
            raise UserAlreadyExistsException("username", username)

        # Create user (password stored as plain text)
        user = await self.repository.create(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
        )

        await self.db.commit()
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(f"id={user_id}")
        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        user = await self.repository.get_by_email(email)
        if not user:
            raise UserNotFoundException(f"email={email}")
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        return await self.repository.get_all(skip=skip, limit=limit)

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination"""
        return await self.repository.get_active_users(skip=skip, limit=limit)

    async def update_user(
        self,
        user_id: int,
        email: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> User:
        """Update user fields"""
        # Check user exists
        user = await self.get_user_by_id(user_id)

        # Prepare update data (only non-None values)
        update_data = {}
        if email is not None:
            if email != user.email and await self.repository.email_exists(email):
                raise UserAlreadyExistsException("email", email)
            update_data["email"] = email

        if username is not None:
            if username != user.username and await self.repository.username_exists(username):
                raise UserAlreadyExistsException("username", username)
            update_data["username"] = username

        if password is not None:
            update_data["password"] = password
        if first_name is not None:
            update_data["first_name"] = first_name
        if last_name is not None:
            update_data["last_name"] = last_name
        if is_active is not None:
            update_data["is_active"] = is_active

        # Update user
        updated_user = await self.repository.update(user_id, **update_data)
        await self.db.commit()

        if not updated_user:
            raise UserNotFoundException(f"id={user_id}")

        return updated_user

    async def delete_user(self, user_id: int) -> bool:
        """Soft delete user (sets is_active=False)"""
        await self.update_user(user_id, is_active=False)
        await self.db.commit()
        return True
