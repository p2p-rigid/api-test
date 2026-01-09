"""
Example service demonstrating Unit of Work pattern for complex operations involving multiple repositories.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.core.uow import UnitOfWork
from app.models.entities.user import User


class UserManagementService:
    """
    Service for complex user management operations that might involve multiple repositories.
    Demonstrates the use of Unit of Work pattern for coordinating operations across multiple repositories.
    """
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self.logger = structlog.get_logger(__name__).bind(service="UserManagementService")

    async def create_user_with_profile(self, user_data: dict, profile_data: dict) -> User:
        """
        Example of a complex operation that creates a user and their profile in a single transaction.
        This demonstrates the use of Unit of Work for coordinating multiple repository operations.
        
        Args:
            user_data: Data for creating the user
            profile_data: Data for creating the user's profile
            
        Returns:
            The created user object
        """
        async with self.uow.transaction():
            # Create user using the user repository
            user_repo = self.uow.users
            user = await user_repo.create(**user_data)
            
            # In a real application, we would also create a profile using a profile repository
            # profile_repo = self.uow.profiles  # Assuming a ProfileRepository exists
            # await profile_repo.create(user_id=user.id, **profile_data)
            
            self.logger.info("User with profile created successfully", user_id=user.id)
            return user

    async def deactivate_user_and_cleanup(self, user_id: int) -> bool:
        """
        Example of a complex operation that deactivates a user and performs cleanup operations
        across multiple repositories in a single transaction.
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            True if the operation was successful, False otherwise
        """
        async with self.uow.transaction():
            # Get user using the user repository
            user_repo = self.uow.users
            user = await user_repo.get_by_id(user_id)
            
            if not user:
                self.logger.warning("Cannot deactivate non-existent user", user_id=user_id)
                return False
            
            # Update user to deactivate
            updated_user = await user_repo.update(user_id, is_active=False)
            
            # In a real application, we would also perform cleanup operations
            # using other repositories, e.g., removing user's posts, notifications, etc.
            # posts_repo = self.uow.posts  # Assuming a PostRepository exists
            # await posts_repo.soft_delete_by_user_id(user_id)
            
            self.logger.info("User deactivated and cleanup completed", user_id=user_id)
            return updated_user is not None