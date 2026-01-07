# User Service Implementation Plan (Simplified - No Security)

**Goal:** Implement a complete user service with controller/service/repository pattern, database migrations, and comprehensive testing. Focus on learning Python API development patterns without security complexity.

**Simplified Approach:**
- Password stored as plain text (for learning purposes only)
- No password hashing or authentication
- No login endpoint
- Focus on CRUD operations and layered architecture

**User Requirements:**
- Standard user fields: id, email, username, password (plain text), first_name, last_name, is_active, timestamps
- Both unit tests (mocked) and integration tests (real DB)
- Step-by-step testable implementation

---

## Phase 1: Database Layer

### Step 1.1: Initialize Alembic ✅ DONE
**Files to create:**
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/` directory

**Actions:**
1. Run `alembic init alembic` from project root
2. Edit `alembic/env.py`:
   - Import `Base` from `app.models.entities.base`
   - Import `settings` from `app.config.settings`
   - Configure async SQLAlchemy engine
   - Set `target_metadata = Base.metadata`

**Key code for alembic/env.py:**
```python
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
import asyncio

from app.config.settings import settings
from app.models.entities.base import Base

config = context.config
config.set_main_option('sqlalchemy.url', settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Test:** `alembic current` should run without errors

---

### Step 1.2: Create User Entity Model ✅ DONE
**File:** `app/models/entities/user.py`

**Implementation:**
```python
from sqlalchemy import String, Boolean, Integer, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.entities.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)  # Plain text for learning
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
```

**Test:** Import the model to verify no syntax errors: `python -c "from app.models.entities.user import User; print('OK')"`

---

### Step 1.3: Generate and Apply Migration ✅ DONE
**File:** `alembic/versions/ea93a95f8f4d_create_users_table.py` (auto-generated)

**Actions:**
1. Run `alembic revision --autogenerate -m "create users table"`
2. Review generated migration
3. Run `alembic upgrade head` to apply migration

**Test:**
- Verify migration applied: `alembic current`
- Verify table created: Connect to DB and check table structure
- Test rollback: `alembic downgrade -1`
- Re-apply: `alembic upgrade head`

---

## Phase 2: Repository Layer

### Step 2.1: Create Base Repository ✅ DONE
**File:** `app/repositories/base.py`

**Implementation:**
```python
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

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

    async def delete(self, id: int) -> bool:
        """Delete a record by ID"""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0
```

**Key Patterns:**
- Generic base class for reusability
- Uses `flush()` instead of `commit()` (commits at service/route level)
- `refresh()` after create to load database defaults

**Test:** Unit test with mocked AsyncSession (Step 5.2)

---

### Step 2.2: Create User Repository ✅ DONE
**File:** `app/repositories/user_repository.py`

**Implementation:**
```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.entities.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity with custom queries"""

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalars().first()

    async def get_active_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all active users"""
        result = await self.db.execute(
            select(User)
            .where(User.is_active == True)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.first() is not None

    async def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        return result.first() is not None
```

**Test:** Unit tests at `tests/unit/test_user_repository.py`

---

## Phase 3: Service Layer

### Step 3.1: Create Custom Exceptions ✅ DONE
**File:** `app/core/exceptions.py`

**Implementation:**
```python
class UserNotFoundException(Exception):
    """Raised when a user is not found"""
    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class UserAlreadyExistsException(Exception):
    """Raised when trying to create a user that already exists"""
    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"User with {field}='{value}' already exists")
```

**Test:** Exception raising in service tests

---

### Step 3.2: Create User Service ✅ DONE
**File:** `app/services/user_service.py`

**Implementation:**
```python
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
```

**Key Features:**
- Simple validation (email/username uniqueness)
- Plain text password storage
- Transaction management with commit
- Soft delete pattern

**Test:** Unit tests at `tests/unit/test_user_service.py` with mocked repository

---

## Phase 4: API Layer

### Step 4.1: Create Pydantic Schemas ✅ DONE
**File:** `app/api/v1/schemas/user_schemas.py`

**Implementation:**
```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=3, max_length=100)


class UserUpdate(BaseModel):
    """Schema for updating a user (all fields optional)"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=3, max_length=100)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
```

**Note:** UserResponse includes password for simplicity (normally excluded)

**Test:** Validated automatically by FastAPI

---

### Step 4.2: Create Exception Handlers ✅ DONE
**File:** `app/api/v1/exception_handlers.py`

**Implementation:**
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
)


async def user_not_found_handler(request: Request, exc: UserNotFoundException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "identifier": exc.identifier},
    )


async def user_already_exists_handler(request: Request, exc: UserAlreadyExistsException) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "field": exc.field,
            "value": exc.value,
        },
    )
```

**Integration:** Register in `app/main.py`:
```python
from app.api.v1.exception_handlers import user_not_found_handler, user_already_exists_handler
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException

app.add_exception_handler(UserNotFoundException, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsException, user_already_exists_handler)
```

**Test:** Integration tests verify correct HTTP status codes

---

### Step 4.3: Create User Routes ✅ DONE
**File:** `app/api/v1/routes/users.py`

**Implementation:**
```python
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.config.database import get_db
from app.services.user_service import UserService
from app.api.v1.schemas.user_schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
)

router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """Dependency injection for UserService"""
    return UserService(db)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service),
):
    """Create a new user"""
    user = await user_service.create_user(
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """Get user by ID"""
    user = await user_service.get_user_by_id(user_id)
    return user


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    active_only: bool = Query(False),
    user_service: UserService = Depends(get_user_service),
):
    """Get all users with pagination"""
    if active_only:
        users = await user_service.get_active_users(skip=skip, limit=limit)
    else:
        users = await user_service.get_all_users(skip=skip, limit=limit)
    return users


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    user_service: UserService = Depends(get_user_service),
):
    """Update user fields"""
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


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(get_user_service),
):
    """Delete user (soft delete)"""
    await user_service.delete_user(user_id)
    return None
```

**Endpoints:**
- `POST /api/v1/users/` - Create user
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/` - List users
- `PATCH /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Soft delete user

**Test:** Integration tests at `tests/integration/test_user_api.py`

---

### Step 4.4: Update Main Application ✅ DONE
**File:** `app/api/v1/router.py` (updated)

**Implementation:**
```python
from fastapi import APIRouter
from app.api.v1.routes import health, users

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

**File:** `app/main.py` (update)

**Add imports and register router:**
```python
from app.api.v1.router import api_router
from app.api.v1.exception_handlers import user_not_found_handler, user_already_exists_handler
from app.core.exceptions import UserNotFoundException, UserAlreadyExistsException

# After app creation, before middleware
app.include_router(api_router, prefix="/api/v1")
app.add_exception_handler(UserNotFoundException, user_not_found_handler)
app.add_exception_handler(UserAlreadyExistsException, user_already_exists_handler)
```

**Test:** Start server and visit `http://localhost:8000/docs`

---

## Phase 5: Testing Infrastructure

### Step 5.1: Setup Test Configuration ✅ DONE
**File:** `tests/conftest.py`

**Implementation:**
```python
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport

from app.config.settings import settings
from app.models.entities.base import Base
from app.main import app
from app.config.database import get_db

# Test database URL (configure in .env or settings)
TEST_DATABASE_URL = settings.database_url.replace("/api_test", "/api_test_db")

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override"""
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def user_data() -> dict:
    """Sample user data for tests"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123",
        "first_name": "Test",
        "last_name": "User",
    }


@pytest.fixture
def user_data_2() -> dict:
    """Second user data for multi-user tests"""
    return {
        "email": "another@example.com",
        "username": "anotheruser",
        "password": "password456",
        "first_name": "Another",
        "last_name": "User",
    }
```

**Files:**
- `tests/__init__.py` (empty file)
- `tests/unit/__init__.py` (empty file)
- `tests/integration/__init__.py` (empty file)

**Test:** `pytest --collect-only` to verify fixtures work

---

### Step 5.2: Unit Tests - Repository ✅ DONE
**File:** `tests/unit/test_user_repository.py`

**Implementation:**
```python
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
```

**Test:** `pytest tests/unit/test_user_repository.py -v`

---

### Step 5.3: Unit Tests - Service ✅ DONE
**File:** `tests/unit/test_user_service.py`

**Implementation:**
```python
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
async def test_get_user_by_id_not_found(user_service):
    """Test get_user_by_id raises exception when user not found"""
    user_service.repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(UserNotFoundException):
        await user_service.get_user_by_id(999)
```

**Test:** `pytest tests/unit/test_user_service.py -v`

---

### Step 5.4: Integration Tests - API ✅ DONE
**File:** `tests/integration/test_user_api.py`

**Implementation:**
```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, user_data: dict):
    """Test POST /api/v1/users/ creates a user"""
    response = await client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, user_data: dict):
    """Test creating user with duplicate email fails"""
    await client.post("/api/v1/users/", json=user_data)

    user_data_2 = user_data.copy()
    user_data_2["username"] = "differentuser"
    response = await client.post("/api/v1/users/", json=user_data_2)

    assert response.status_code == 409
    data = response.json()
    assert "email" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_user_by_id(client: AsyncClient, user_data: dict):
    """Test GET /api/v1/users/{id} retrieves user"""
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """Test GET /api/v1/users/{id} returns 404 for non-existent user"""
    response = await client.get("/api/v1/users/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, user_data: dict):
    """Test PATCH /api/v1/users/{id} updates user"""
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    update_data = {"first_name": "Updated", "last_name": "Name"}
    response = await client.patch(f"/api/v1/users/{user_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "Name"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, user_data: dict):
    """Test DELETE /api/v1/users/{id} soft deletes user"""
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204

    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test GET /api/v1/users/ returns all users"""
    await client.post("/api/v1/users/", json=user_data)
    await client.post("/api/v1/users/", json=user_data_2)

    response = await client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
```

**Test:** `pytest tests/integration/test_user_api.py -v`

---

## Critical Files Summary

**New files (14 total):**
1. `app/models/entities/user.py` - User entity
2. `app/repositories/base.py` - Base repository
3. `app/repositories/user_repository.py` - User repository
4. `app/core/exceptions.py` - Custom exceptions
5. `app/services/user_service.py` - User service
6. `app/api/v1/schemas/user_schemas.py` - Pydantic schemas
7. `app/api/v1/exception_handlers.py` - Exception handlers
8. `app/api/v1/routes/users.py` - User routes
9. `app/api/v1/router.py` - API router
10. `alembic.ini` - Alembic config
11. `alembic/env.py` - Alembic environment
12. `tests/conftest.py` - Test fixtures
13. `tests/unit/test_user_repository.py` - Repository tests
14. `tests/unit/test_user_service.py` - Service tests
15. `tests/integration/test_user_api.py` - API tests

**Modified files (1):**
1. `app/main.py` - Register routes and exception handlers

**New directories:**
- `app/core/`
- `app/api/v1/schemas/`
- `tests/unit/`
- `tests/integration/`
- `alembic/`

---

## Execution Order

1. **Database:** Steps 1.1 → 1.2 → 1.3
2. **Repository:** Steps 2.1 → 2.2
3. **Service:** Steps 3.1 → 3.2
4. **API:** Steps 4.1 → 4.2 → 4.3 → 4.4
5. **Testing:** Steps 5.1 → 5.2 → 5.3 → 5.4

**Each step is independently testable.**

---

## Running the System

**Setup test database:**
```bash
# Create test database
createdb api_test_db
```

**Apply migrations:**
```bash
alembic upgrade head
```

**Start server:**
```bash
uvicorn app.main:app --reload
```

**Run tests:**
```bash
# All tests
pytest -v

# With coverage
pytest -v --cov=app --cov-report=html

# Specific test file
pytest tests/integration/test_user_api.py -v
```

**Test API manually:**
```bash
# Create user
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "username": "testuser", "password": "pass123", "first_name": "Test", "last_name": "User"}'

# Get user
curl "http://localhost:8000/api/v1/users/1"

# List users
curl "http://localhost:8000/api/v1/users/?skip=0&limit=10"

# Update user
curl -X PATCH "http://localhost:8000/api/v1/users/1" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Updated"}'

# Delete user
curl -X DELETE "http://localhost:8000/api/v1/users/1"
```

**View API docs:**
- OpenAPI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Key Learning Points

**Layered Architecture:**
- **Models**: Database entities (SQLAlchemy ORM)
- **Repositories**: Data access (CRUD operations)
- **Services**: Business logic (validation, transactions)
- **Routes**: HTTP endpoints (request/response)
- **Schemas**: Data validation (Pydantic)

**Async Pattern:**
- All database operations use async/await
- FastAPI endpoints are async
- AsyncSession for SQLAlchemy

**Dependency Injection:**
- Services injected via `Depends()`
- Makes testing easier (can mock dependencies)

**Testing Strategy:**
- Unit tests: Mock dependencies, test isolation
- Integration tests: Real database, test full stack
- Each test has clean database state

**Next Steps (Later):**
- Add Google Agent Development Kit orchestration
- Add JWT authentication (when ready)
- Add more complex business logic
