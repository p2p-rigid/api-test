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
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client: AsyncClient, user_data: dict):
    """Test creating user with duplicate email fails"""
    await client.post("/api/v1/users/", json=user_data)

    user_data_2 = user_data.copy()
    user_data_2["username"] = "differentuser"
    response = await client.post("/api/v1/users/", json=user_data_2)

    assert response.status_code == 409
    data = response.json()
    assert data["error_code"] == "USER_ALREADY_EXISTS"
    assert data["field"] == "email"


@pytest.mark.asyncio
async def test_create_user_duplicate_username(client: AsyncClient, user_data: dict):
    """Test creating user with duplicate username fails"""
    await client.post("/api/v1/users/", json=user_data)

    user_data_2 = user_data.copy()
    user_data_2["email"] = "different@example.com"
    response = await client.post("/api/v1/users/", json=user_data_2)

    assert response.status_code == 409
    data = response.json()
    assert data["error_code"] == "USER_ALREADY_EXISTS"
    assert data["field"] == "username"


@pytest.mark.asyncio
async def test_create_user_invalid_email(client: AsyncClient, user_data: dict):
    """Test creating user with invalid email fails validation"""
    user_data["email"] = "not-an-email"
    response = await client.post("/api/v1/users/", json=user_data)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_user_missing_fields(client: AsyncClient):
    """Test creating user with missing required fields fails"""
    response = await client.post("/api/v1/users/", json={"email": "test@example.com"})

    assert response.status_code == 422


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
    assert data["username"] == user_data["username"]


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    """Test GET /api/v1/users/{id} returns 404 for non-existent user"""
    response = await client.get("/api/v1/users/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_all_users(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test GET /api/v1/users/ returns all users"""
    await client.post("/api/v1/users/", json=user_data)
    await client.post("/api/v1/users/", json=user_data_2)

    response = await client.get("/api/v1/users/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_users_pagination(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test GET /api/v1/users/ with pagination parameters"""
    await client.post("/api/v1/users/", json=user_data)
    await client.post("/api/v1/users/", json=user_data_2)

    response = await client.get("/api/v1/users/?skip=0&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_get_active_users_only(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test GET /api/v1/users/?active_only=true returns only active users"""
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]
    await client.post("/api/v1/users/", json=user_data_2)

    # Deactivate first user
    await client.delete(f"/api/v1/users/{user_id}")

    response = await client.get("/api/v1/users/?active_only=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == user_data_2["email"]


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
    assert data["email"] == user_data["email"]  # unchanged


@pytest.mark.asyncio
async def test_update_user_email(client: AsyncClient, user_data: dict):
    """Test PATCH /api/v1/users/{id} can update email"""
    create_response = await client.post("/api/v1/users/", json=user_data)
    user_id = create_response.json()["id"]

    update_data = {"email": "newemail@example.com"}
    response = await client.patch(f"/api/v1/users/{user_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient):
    """Test PATCH /api/v1/users/{id} returns 404 for non-existent user"""
    update_data = {"first_name": "Updated"}
    response = await client.patch("/api/v1/users/999", json=update_data)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_duplicate_email(client: AsyncClient, user_data: dict, user_data_2: dict):
    """Test PATCH /api/v1/users/{id} fails when email conflicts"""
    await client.post("/api/v1/users/", json=user_data)
    create_response_2 = await client.post("/api/v1/users/", json=user_data_2)
    user_id_2 = create_response_2.json()["id"]

    update_data = {"email": user_data["email"]}  # try to use first user's email
    response = await client.patch(f"/api/v1/users/{user_id_2}", json=update_data)

    assert response.status_code == 409


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
async def test_delete_user_not_found(client: AsyncClient):
    """Test DELETE /api/v1/users/{id} returns 404 for non-existent user"""
    response = await client.delete("/api/v1/users/999")
    assert response.status_code == 404
