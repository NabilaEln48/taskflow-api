from fastapi import status

def test_register_creates_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "nabila@example.com", "password": "supersecret"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    body = response.json()
    assert body["email"] == "nabila@example.com"
    assert "id" in body

    assert "password" not in body
    assert "hashed_password" not in body

def test_register_rejects_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "secret123"}
    assert client.post("/auth/register", json=payload).status_code == 201
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_409_CONFLICT

def test_register_rejects_invalid_email(client):
    response = client.post(
        "/auth/register", json={"email": "not-an-email", "password": "secret123"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

def test_login_returns_bearer_token(client):
    client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "secret123"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "secret123"},
    )
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]

def test_login_rejects_wrong_password(client):
    client.post(
        "/auth/register",
        json={"email": "wrongpw@example.com", "password": "correct-horse"},
    )
    response = client.post(
        "/auth/login",
        data={"username": "wrongpw@example.com", "password": "wrong-horse"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_rejects_unknown_email(client):

    response = client.post(
        "/auth/login",
        data={"username": "nobody@example.com", "password": "whatever"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_protected_route_rejects_missing_token(client):
    response = client.get("/tasks")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_protected_route_rejects_bad_token(client):
    response = client.get("/tasks", headers={"Authorization": "Bearer garbage"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
