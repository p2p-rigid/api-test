from fastapi import APIRouter, Depends, status, Query
from typing import List

from app.dependencies import get_user_service
from app.services.user_service import UserService
from app.api.v1.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
)

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED, summary="Create a new user", description="Creates a new user with the provided details.")
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Create a new user.

    Args:
        user_data (UserCreate): The user data to create the user with.
        user_service (UserService): The user service dependency.

    Returns:
        UserResponse: The created user object.

    Raises:
        HTTPException: If the email or username already exists.
    """
    user = await user_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    return user


@router.get("/{user_id}", response_model=UserResponse, summary="Get user by ID", description="Retrieves a user by their unique ID.")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Get a user by their ID.

    Args:
        user_id (int): The ID of the user to retrieve.
        user_service (UserService): The user service dependency.

    Returns:
        UserResponse: The user object if found.

    Raises:
        HTTPException: If the user is not found.
    """
    user = await user_service.get_user_by_id(user_id)
    return user


@router.get("/", response_model=List[UserResponse], summary="Get all users", description="Retrieves all users with optional pagination and filtering.")
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    user_service: UserService = Depends(get_user_service),
):
    """
    Get all users with pagination.

    Args:
        skip (int): Number of users to skip for pagination.
        limit (int): Maximum number of users to return.
        active_only (bool): Whether to return only active users.
        user_service (UserService): The user service dependency.

    Returns:
        List[UserResponse]: A list of user objects.
    """
    if active_only:
        users = await user_service.get_active_users(skip=skip, limit=limit)
    else:
        users = await user_service.get_all_users(skip=skip, limit=limit)
    return users


@router.patch("/{user_id}", response_model=UserResponse, summary="Update user", description="Updates specific fields of an existing user.")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """
    Update user fields.

    Args:
        user_id (int): The ID of the user to update.
        user_data (UserUpdate): The fields to update.
        user_service (UserService): The user service dependency.

    Returns:
        UserResponse: The updated user object.

    Raises:
        HTTPException: If the user is not found or if the new email/username already exists.
    """
    user = await user_service.update_user(
        user_id=user_id,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=user_data.is_active,
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete user", description="Deletes a user (soft delete by setting is_active to False).")
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """
    Delete a user (soft delete).

    Args:
        user_id (int): The ID of the user to delete.
        user_service (UserService): The user service dependency.

    Returns:
        None: Returns no content on successful deletion.

    Raises:
        HTTPException: If the user is not found.
    """
    await user_service.delete_user(user_id)
    return None
