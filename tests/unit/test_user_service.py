"""
Unit tests for UserService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.models.entities.user import User
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_user_repository():
    """Mock user repository for testing."""
    repo = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_by_email = AsyncMock()
    repo.get_by_username = AsyncMock()
    repo.get_all = AsyncMock()
    repo.get_active_users = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.email_exists = AsyncMock()
    repo.username_exists = AsyncMock()
    return repo


@pytest.fixture
def user_service(mock_db_session, mock_user_repository):
    """Create a UserService instance with mocked dependencies."""
    service = UserService(mock_db_session)
    service.repository = mock_user_repository
    return service


@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_user_repository):
    """Test successful user creation."""
    # Arrange
    email = "test@example.com"
    username = "testuser"
    password = "Password123!"
    first_name = "Test"
    last_name = "User"
    
    mock_user_repository.email_exists.return_value = False
    mock_user_repository.username_exists.return_value = False
    
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = email
    mock_user.username = username
    mock_user_repository.create.return_value = mock_user

    # Act
    result = await user_service.create_user(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name
    )

    # Assert
    assert result == mock_user
    mock_user_repository.email_exists.assert_called_once_with(email)
    mock_user_repository.username_exists.assert_called_once_with(username)
    mock_user_repository.create.assert_called_once_with(
        email=email,
        username=username,
        password=password,
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_create_user_email_exists(user_service, mock_user_repository):
    """Test user creation fails when email already exists."""
    # Arrange
    email = "test@example.com"
    username = "testuser"
    password = "Password123!"
    first_name = "Test"
    last_name = "User"
    
    mock_user_repository.email_exists.return_value = True

    # Act & Assert
    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
    
    assert exc_info.value.field == "email"
    assert exc_info.value.value == email
    mock_user_repository.email_exists.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_create_user_username_exists(user_service, mock_user_repository):
    """Test user creation fails when username already exists."""
    # Arrange
    email = "test@example.com"
    username = "testuser"
    password = "Password123!"
    first_name = "Test"
    last_name = "User"
    
    mock_user_repository.email_exists.return_value = False
    mock_user_repository.username_exists.return_value = True

    # Act & Assert
    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
    
    assert exc_info.value.field == "username"
    assert exc_info.value.value == username
    mock_user_repository.email_exists.assert_called_once_with(email)
    mock_user_repository.username_exists.assert_called_once_with(username)


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service, mock_user_repository):
    """Test successful retrieval of user by ID."""
    # Arrange
    user_id = 1
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_user_repository.get_by_id.return_value = mock_user

    # Act
    result = await user_service.get_user_by_id(user_id)

    # Assert
    assert result == mock_user
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service, mock_user_repository):
    """Test retrieval of user by ID fails when user doesn't exist."""
    # Arrange
    user_id = 1
    mock_user_repository.get_by_id.return_value = None

    # Act & Assert
    with pytest.raises(UserNotFoundException):
        await user_service.get_user_by_id(user_id)
    
    mock_user_repository.get_by_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_get_user_by_email_success(user_service, mock_user_repository):
    """Test successful retrieval of user by email."""
    # Arrange
    email = "test@example.com"
    mock_user = MagicMock(spec=User)
    mock_user.email = email
    mock_user_repository.get_by_email.return_value = mock_user

    # Act
    result = await user_service.get_user_by_email(email)

    # Assert
    assert result == mock_user
    mock_user_repository.get_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service, mock_user_repository):
    """Test retrieval of user by email fails when user doesn't exist."""
    # Arrange
    email = "test@example.com"
    mock_user_repository.get_by_email.return_value = None

    # Act & Assert
    with pytest.raises(UserNotFoundException):
        await user_service.get_user_by_email(email)
    
    mock_user_repository.get_by_email.assert_called_once_with(email)


@pytest.mark.asyncio
async def test_get_all_users_success(user_service, mock_user_repository):
    """Test successful retrieval of all users."""
    # Arrange
    mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_user_repository.get_all.return_value = mock_users

    # Act
    result = await user_service.get_all_users(skip=0, limit=10)

    # Assert
    assert result == mock_users
    mock_user_repository.get_all.assert_called_once_with(skip=0, limit=10)


@pytest.mark.asyncio
async def test_get_active_users_success(user_service, mock_user_repository):
    """Test successful retrieval of active users."""
    # Arrange
    mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_user_repository.filter.return_value = mock_users

    # Act
    result = await user_service.get_active_users(skip=0, limit=10)

    # Assert
    assert result == mock_users
    mock_user_repository.filter.assert_called_once_with(skip=0, limit=10, is_active=True)


@pytest.mark.asyncio
async def test_update_user_success(user_service, mock_user_repository):
    """Test successful user update."""
    # Arrange
    user_id = 1
    new_email = "newemail@example.com"
    
    mock_existing_user = MagicMock(spec=User)
    mock_existing_user.id = user_id
    mock_existing_user.email = "old@example.com"
    mock_existing_user.username = "testuser"
    
    mock_updated_user = MagicMock(spec=User)
    mock_updated_user.id = user_id
    mock_updated_user.email = new_email
    
    user_service.get_user_by_id = AsyncMock(return_value=mock_existing_user)
    mock_user_repository.email_exists.return_value = False
    mock_user_repository.update.return_value = mock_updated_user

    # Act
    result = await user_service.update_user(user_id=user_id, email=new_email)

    # Assert
    assert result == mock_updated_user
    mock_user_repository.update.assert_called_once_with(user_id, email=new_email)


@pytest.mark.asyncio
async def test_update_user_email_exists(user_service, mock_user_repository):
    """Test user update fails when new email already exists."""
    # Arrange
    user_id = 1
    new_email = "existing@example.com"
    
    mock_existing_user = MagicMock(spec=User)
    mock_existing_user.id = user_id
    mock_existing_user.email = "old@example.com"
    mock_existing_user.username = "testuser"
    
    user_service.get_user_by_id = AsyncMock(return_value=mock_existing_user)
    mock_user_repository.email_exists.return_value = True

    # Act & Assert
    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.update_user(user_id=user_id, email=new_email)
    
    assert exc_info.value.field == "email"
    assert exc_info.value.value == new_email


@pytest.mark.asyncio
async def test_delete_user_success(user_service, mock_user_repository):
    """Test successful user deletion (soft delete)."""
    # Arrange
    user_id = 1
    
    mock_existing_user = MagicMock(spec=User)
    mock_existing_user.id = user_id
    mock_existing_user.email = "test@example.com"
    mock_existing_user.username = "testuser"
    
    user_service.get_user_by_id = AsyncMock(return_value=mock_existing_user)
    user_service.update_user = AsyncMock()

    # Act
    result = await user_service.delete_user(user_id)

    # Assert
    assert result is True
    user_service.update_user.assert_called_once_with(user_id, is_active=False)