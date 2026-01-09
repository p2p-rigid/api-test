"""
Unit tests for UserRepository.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.repositories.user_repository import UserRepository
from app.models.entities.user import User


@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def user_repository(mock_db_session):
    """Create a UserRepository instance with mocked dependencies."""
    return UserRepository(mock_db_session)


@pytest.mark.asyncio
async def test_get_by_email_success(user_repository, mock_db_session):
    """Test successful retrieval of user by email."""
    # Arrange
    email = "test@example.com"
    mock_user = MagicMock(spec=User)
    mock_scalars_result = MagicMock()
    mock_scalars_result.first.return_value = mock_user
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.get_by_email(email)

    # Assert
    assert result == mock_user
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_username_success(user_repository, mock_db_session):
    """Test successful retrieval of user by username."""
    # Arrange
    username = "testuser"
    mock_user = MagicMock(spec=User)
    mock_scalars_result = MagicMock()
    mock_scalars_result.first.return_value = mock_user
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.get_by_username(username)

    # Assert
    assert result == mock_user
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_users_success(user_repository, mock_db_session):
    """Test successful retrieval of active users."""
    # Arrange
    mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_scalars_result = MagicMock()
    mock_scalars_result.all.return_value = mock_users
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.get_active_users(skip=0, limit=10)

    # Assert
    assert result == mock_users
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_email_exists_true(user_repository, mock_db_session):
    """Test checking if email exists returns True."""
    # Arrange
    email = "test@example.com"
    mock_result = AsyncMock()
    mock_result.first.return_value = MagicMock()  # A result means it exists
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await user_repository.email_exists(email)

    # Assert
    assert result is True
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_email_exists_false(user_repository, mock_db_session):
    """Test checking if email exists returns False."""
    # Arrange
    email = "test@example.com"
    mock_execute_result = MagicMock()
    mock_execute_result.first.return_value = None  # No result means it doesn't exist
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.email_exists(email)

    # Assert
    assert result is False
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_username_exists_true(user_repository, mock_db_session):
    """Test checking if username exists returns True."""
    # Arrange
    username = "testuser"
    mock_result = AsyncMock()
    mock_result.first.return_value = MagicMock()  # A result means it exists
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await user_repository.username_exists(username)

    # Assert
    assert result is True
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_username_exists_false(user_repository, mock_db_session):
    """Test checking if username exists returns False."""
    # Arrange
    username = "testuser"
    mock_execute_result = MagicMock()
    mock_execute_result.first.return_value = None  # No result means it doesn't exist
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.username_exists(username)

    # Assert
    assert result is False
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_success(user_repository, mock_db_session):
    """Test successful user creation."""
    # Arrange
    email = "test@example.com"
    username = "testuser"
    mock_user = MagicMock(spec=User)
    user_repository.model = MagicMock(return_value=mock_user)

    # Act
    result = await user_repository.create(
        email=email,
        username=username,
        password="Password123!",
        first_name="Test",
        last_name="User"
    )

    # Assert
    assert result == mock_user
    mock_db_session.add.assert_called_once_with(mock_user)
    mock_db_session.flush.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(mock_user)


@pytest.mark.asyncio
async def test_get_by_id_success(user_repository, mock_db_session):
    """Test successful retrieval of user by ID."""
    # Arrange
    user_id = 1
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_scalars_result = MagicMock()
    mock_scalars_result.first.return_value = mock_user
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.get_by_id(user_id)

    # Assert
    assert result == mock_user
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_all_success(user_repository, mock_db_session):
    """Test successful retrieval of all users."""
    # Arrange
    mock_users = [MagicMock(spec=User), MagicMock(spec=User)]
    mock_scalars_result = MagicMock()
    mock_scalars_result.all.return_value = mock_users
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.get_all(skip=0, limit=10)

    # Assert
    assert result == mock_users
    mock_db_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_success(user_repository, mock_db_session):
    """Test successful user update."""
    # Arrange
    user_id = 1
    new_email = "newemail@example.com"
    mock_user = MagicMock(spec=User)
    mock_user.id = user_id
    mock_scalars_result = MagicMock()
    mock_scalars_result.first.return_value = mock_user
    mock_execute_result = MagicMock()
    mock_execute_result.scalars.return_value = mock_scalars_result
    mock_db_session.execute.return_value = mock_execute_result

    # Act
    result = await user_repository.update(user_id, email=new_email)

    # Assert
    assert result == mock_user
    mock_db_session.execute.assert_called_once()
    mock_db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_delete_user_success(user_repository, mock_db_session):
    """Test successful user deletion."""
    # Arrange
    user_id = 1
    mock_result = AsyncMock()
    mock_result.rowcount = 1  # Indicate one row was affected
    mock_db_session.execute.return_value = mock_result

    # Act
    result = await user_repository.delete(user_id)

    # Assert
    assert result is True
    mock_db_session.execute.assert_called_once()
    mock_db_session.flush.assert_called_once()