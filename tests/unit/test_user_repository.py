import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.models.entities.user import User


@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_db):
    """Create UserRepository with mocked DB"""
    return UserRepository(mock_db)


@pytest.mark.asyncio
async def test_get_by_email(user_repository, mock_db):
    """Test get_by_email returns user"""
    expected_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    mock_result = MagicMock()
    mock_result.scalars().first.return_value = expected_user
    mock_db.execute.return_value = mock_result

    user = await user_repository.get_by_email("test@example.com")

    assert user == expected_user
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_email_not_found(user_repository, mock_db):
    """Test get_by_email returns None when user not found"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db.execute.return_value = mock_result

    user = await user_repository.get_by_email("nonexistent@example.com")

    assert user is None


@pytest.mark.asyncio
async def test_get_by_username(user_repository, mock_db):
    """Test get_by_username returns user"""
    expected_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    mock_result = MagicMock()
    mock_result.scalars().first.return_value = expected_user
    mock_db.execute.return_value = mock_result

    user = await user_repository.get_by_username("testuser")

    assert user == expected_user
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_email_exists_true(user_repository, mock_db):
    """Test email_exists returns True when email exists"""
    mock_result = MagicMock()
    mock_result.first.return_value = (1,)
    mock_db.execute.return_value = mock_result

    exists = await user_repository.email_exists("test@example.com")

    assert exists is True


@pytest.mark.asyncio
async def test_email_exists_false(user_repository, mock_db):
    """Test email_exists returns False when email doesn't exist"""
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_db.execute.return_value = mock_result

    exists = await user_repository.email_exists("nonexistent@example.com")

    assert exists is False


@pytest.mark.asyncio
async def test_username_exists_true(user_repository, mock_db):
    """Test username_exists returns True when username exists"""
    mock_result = MagicMock()
    mock_result.first.return_value = (1,)
    mock_db.execute.return_value = mock_result

    exists = await user_repository.username_exists("testuser")

    assert exists is True


@pytest.mark.asyncio
async def test_username_exists_false(user_repository, mock_db):
    """Test username_exists returns False when username doesn't exist"""
    mock_result = MagicMock()
    mock_result.first.return_value = None
    mock_db.execute.return_value = mock_result

    exists = await user_repository.username_exists("nonexistentuser")

    assert exists is False


@pytest.mark.asyncio
async def test_get_active_users(user_repository, mock_db):
    """Test get_active_users returns list of active users"""
    expected_users = [
        User(
            id=1,
            email="test1@example.com",
            username="testuser1",
            password="password123",
            first_name="Test1",
            last_name="User",
            is_active=True,
        ),
        User(
            id=2,
            email="test2@example.com",
            username="testuser2",
            password="password456",
            first_name="Test2",
            last_name="User",
            is_active=True,
        ),
    ]

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = expected_users
    mock_db.execute.return_value = mock_result

    users = await user_repository.get_active_users(skip=0, limit=100)

    assert len(users) == 2
    assert users == expected_users
