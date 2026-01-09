from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.repositories.user_repository import UserRepository
from app.models.entities.user import User
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
)
from app.services.base_service import BaseService


class UserService(BaseService[User]):
    """Service layer for user business logic"""

    def __init__(self, db: AsyncSession):
        super().__init__(db, UserRepository(db))

    async def create_user(
        self,
        email: str,
        username: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        """Create a new user"""
        self.logger.info("Creating user", email=email, username=username)

        # Check if email already exists
        if await self.repository.email_exists(email):
            self.logger.warning("Email already exists", email=email)
            raise UserAlreadyExistsException("email", email)

        # Check if username already exists
        if await self.repository.username_exists(username):
            self.logger.warning("Username already exists", username=username)
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
        self.logger.info("User created successfully", user_id=user.id, email=email)
        return user

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        self.logger.info("Fetching user by ID", user_id=user_id)
        user = await super().get_by_id(user_id)
        if not user:
            self.logger.warning("User not found", user_id=user_id)
            raise UserNotFoundException(f"id={user_id}")
        self.logger.info("User fetched successfully", user_id=user.id)
        return user

    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        self.logger.info("Fetching user by email", email=email)
        user = await self.repository.get_by_email(email)
        if not user:
            self.logger.warning("User not found", email=email)
            raise UserNotFoundException(f"email={email}")
        self.logger.info("User fetched successfully", user_id=user.id, email=email)
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        self.logger.info("Fetching all users", skip=skip, limit=limit)
        users = await super().get_all(skip=skip, limit=limit)
        self.logger.info("Users fetched successfully", count=len(users))
        return users

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get active users with pagination"""
        self.logger.info("Fetching active users", skip=skip, limit=limit)
        users = await super().filter(skip=skip, limit=limit, is_active=True)
        self.logger.info("Active users fetched successfully", count=len(users))
        return users

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
        self.logger.info("Updating user", user_id=user_id, update_fields=list(filter(None, [email, username, password, first_name, last_name, is_active])))

        # Check user exists
        user = await self.get_user_by_id(user_id)

        # Prepare update data (only non-None values)
        update_data = {}
        if email is not None:
            if email != user.email and await self.repository.email_exists(email):
                self.logger.warning("Email already exists", email=email)
                raise UserAlreadyExistsException("email", email)
            update_data["email"] = email

        if username is not None:
            if username != user.username and await self.repository.username_exists(username):
                self.logger.warning("Username already exists", username=username)
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

        # Update user using base class method
        updated_user = await super().update(user_id, **update_data)

        if not updated_user:
            self.logger.error("Failed to update user", user_id=user_id)
            raise UserNotFoundException(f"id={user_id}")

        self.logger.info("User updated successfully", user_id=updated_user.id)
        return updated_user

    async def delete_user(self, user_id: int) -> bool:
        """Soft delete user (sets is_active=False)"""
        self.logger.info("Soft deleting user", user_id=user_id)
        await self.update_user(user_id, is_active=False)
        self.logger.info("User soft deleted successfully", user_id=user_id)
        return True
