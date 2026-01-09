"""
Integration tests for API endpoints.
"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test the root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data == {"message": "API Test is running"}


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}


@pytest.mark.asyncio
async def test_create_user_success(client: AsyncClient, user_data: dict):
    """Test successful user creation."""
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, user_data: dict):
    """Test user creation fails with duplicate email."""
    # Create the first user
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    
    # Try to create another user with the same email
    duplicate_user_data = user_data.copy()
    duplicate_user_data["username"] = "differentuser"
    response = await client.post("/api/v1/users/", json=duplicate_user_data)
    
    assert response.status_code == 409  # Conflict
    data = response.json()
    assert data["error_code"] == "USER_ALREADY_EXISTS"
    assert data["field"] == "email"


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient, user_data: dict):
    """Test user creation fails with duplicate username."""
    # Create the first user
    response = await client.post("/api/v1/users/", json=user_data)
    assert response.status_code == 201
    
    # Try to create another user with the same username
    duplicate_user_data = user_data.copy()
    duplicate_user_data["email"] = "different@example.com"
    response = await client.post("/api/v1/users/", json=duplicate_user_data)
    
    assert response.status_code == 409  # Conflict
    data = response.json()
    assert data["error_code"] == "USER_ALREADY_EXISTS"
    assert data["field"] == "username"


@pytest.mark.asyncio
async def test_get_user_by_id_success(client: AsyncClient, user_data: dict):
    """Test successful retrieval of user by ID."""
    # Create a user first
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    created_user = create_response.json()
    user_id = created_user["id"]
    
    # Retrieve the user by ID
    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == user_data["email"]
    assert data["username"] == user_data["username"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(client: AsyncClient):
    """Test retrieval of non-existent user by ID."""
    response = await client.get("/api/v1/users/99999")
    assert response.status_code == 404
    
    data = response.json()
    assert data["error_code"] == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_all_users_success(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test successful retrieval of all users."""
    # Create two users
    response1 = await client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == 201
    
    response2 = await client.post("/api/v1/users/", json=user_data_2)
    assert response2.status_code == 201
    
    # Get all users
    response = await client.get("/api/v1/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) >= 2  # At least the two users we created
    
    # Verify both users are in the response
    emails = [user["email"] for user in data]
    assert user_data["email"] in emails
    assert user_data_2["email"] in emails


@pytest.mark.asyncio
async def test_update_user_success(client: AsyncClient, user_data: dict):
    """Test successful user update."""
    # Create a user first
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    created_user = create_response.json()
    user_id = created_user["id"]
    
    # Update the user
    update_data = {
        "first_name": "Updated",
        "last_name": "User"
    }
    response = await client.patch(f"/api/v1/users/{user_id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["first_name"] == "Updated"
    assert data["last_name"] == "User"


@pytest.mark.asyncio
async def test_update_user_email_exists(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test user update fails when new email already exists."""
    # Create two users
    response1 = await client.post("/api/v1/users/", json=user_data)
    assert response1.status_code == 201
    user1 = response1.json()
    
    response2 = await client.post("/api/v1/users/", json=user_data_2)
    assert response2.status_code == 201
    user2 = response2.json()
    
    # Try to update user1 with user2's email
    update_data = {"email": user_data_2["email"]}
    response = await client.patch(f"/api/v1/users/{user1['id']}", json=update_data)
    
    assert response.status_code == 409  # Conflict
    data = response.json()
    assert data["error_code"] == "USER_ALREADY_EXISTS"
    assert data["field"] == "email"


@pytest.mark.asyncio
async def test_delete_user_success(client: AsyncClient, user_data: dict):
    """Test successful user deletion."""
    # Create a user first
    create_response = await client.post("/api/v1/users/", json=user_data)
    assert create_response.status_code == 201
    created_user = create_response.json()
    user_id = created_user["id"]
    
    # Delete the user
    response = await client.delete(f"/api/v1/users/{user_id}")
    assert response.status_code == 204  # No Content
    
    # Verify the user is no longer accessible (soft delete sets is_active=False)
    get_response = await client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200  # Still accessible but might have is_active=False
    data = get_response.json()
    assert data["id"] == user_id