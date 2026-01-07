import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.user_service import UserService
from app.models.entities.user import User
from app.core.exceptions import UserAlreadyExistsException, UserNotFoundException


@pytest.fixture
def mock_db():
    """Mock AsyncSession"""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    return db


@pytest.fixture
def user_service(mock_db):
    """Create UserService with mocked DB"""
    return UserService(mock_db)


@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_db):
    """Test successful user creation"""
    user_service.repository.email_exists = AsyncMock(return_value=False)
    user_service.repository.username_exists = AsyncMock(return_value=False)
    user_service.repository.create = AsyncMock(return_value=User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    ))

    user = await user_service.create_user(
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
    )

    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.password == "password123"
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_email_exists(user_service):
    """Test user creation fails when email exists"""
    user_service.repository.email_exists = AsyncMock(return_value=True)

    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.create_user(
            email="existing@example.com",
            username="newuser",
            password="password",
            first_name="Test",
            last_name="User",
        )

    assert exc_info.value.field == "email"
    assert exc_info.value.value == "existing@example.com"


@pytest.mark.asyncio
async def test_create_user_username_exists(user_service):
    """Test user creation fails when username exists"""
    user_service.repository.email_exists = AsyncMock(return_value=False)
    user_service.repository.username_exists = AsyncMock(return_value=True)

    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.create_user(
            email="new@example.com",
            username="existinguser",
            password="password",
            first_name="Test",
            last_name="User",
        )

    assert exc_info.value.field == "username"
    assert exc_info.value.value == "existinguser"


@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service):
    """Test get_user_by_id returns user when found"""
    expected_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    user_service.repository.get_by_id = AsyncMock(return_value=expected_user)

    user = await user_service.get_user_by_id(1)

    assert user == expected_user
    user_service.repository.get_by_id.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service):
    """Test get_user_by_id raises exception when user not found"""
    user_service.repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException) as exc_info:
        await user_service.get_user_by_id(999)

    assert "id=999" in exc_info.value.identifier


@pytest.mark.asyncio
async def test_get_user_by_email_success(user_service):
    """Test get_user_by_email returns user when found"""
    expected_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    user_service.repository.get_by_email = AsyncMock(return_value=expected_user)

    user = await user_service.get_user_by_email("test@example.com")

    assert user == expected_user


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service):
    """Test get_user_by_email raises exception when user not found"""
    user_service.repository.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException) as exc_info:
        await user_service.get_user_by_email("nonexistent@example.com")

    assert "email=nonexistent@example.com" in exc_info.value.identifier


@pytest.mark.asyncio
async def test_get_all_users(user_service):
    """Test get_all_users returns list of users"""
    expected_users = [
        User(id=1, email="test1@example.com", username="user1", password="pass1", first_name="Test1", last_name="User", is_active=True),
        User(id=2, email="test2@example.com", username="user2", password="pass2", first_name="Test2", last_name="User", is_active=True),
    ]
    user_service.repository.get_all = AsyncMock(return_value=expected_users)

    users = await user_service.get_all_users(skip=0, limit=100)

    assert len(users) == 2
    assert users == expected_users


@pytest.mark.asyncio
async def test_update_user_success(user_service, mock_db):
    """Test update_user updates user fields"""
    existing_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    updated_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Updated",
        last_name="Name",
        is_active=True,
    )

    user_service.repository.get_by_id = AsyncMock(return_value=existing_user)
    user_service.repository.update = AsyncMock(return_value=updated_user)

    user = await user_service.update_user(user_id=1, first_name="Updated", last_name="Name")

    assert user.first_name == "Updated"
    assert user.last_name == "Name"
    mock_db.commit.assert_called()


@pytest.mark.asyncio
async def test_update_user_email_conflict(user_service):
    """Test update_user fails when new email already exists"""
    existing_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    user_service.repository.get_by_id = AsyncMock(return_value=existing_user)
    user_service.repository.email_exists = AsyncMock(return_value=True)

    with pytest.raises(UserAlreadyExistsException) as exc_info:
        await user_service.update_user(user_id=1, email="existing@example.com")

    assert exc_info.value.field == "email"


@pytest.mark.asyncio
async def test_update_user_not_found(user_service):
    """Test update_user fails when user doesn't exist"""
    user_service.repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException):
        await user_service.update_user(user_id=999, first_name="Test")


@pytest.mark.asyncio
async def test_delete_user_success(user_service, mock_db):
    """Test delete_user soft deletes user (sets is_active=False)"""
    existing_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    deactivated_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        password="password123",
        first_name="Test",
        last_name="User",
        is_active=False,
    )

    user_service.repository.get_by_id = AsyncMock(return_value=existing_user)
    user_service.repository.update = AsyncMock(return_value=deactivated_user)

    result = await user_service.delete_user(1)

    assert result is True
    user_service.repository.update.assert_called_once()
