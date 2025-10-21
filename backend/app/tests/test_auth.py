import pytest

def test_register_user(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPass123!"
    })

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"
    assert data["is_active"] == True
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_email(client):
    client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "TestPass123!"
    })
    response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "TestPass123!"
    })

    assert response.status_code == 400
    assert "email ya esta registrado a un usuario" in response.json()["detail"].lower()

def test_register_duplicate_username(client):
    client.post("/auth/register", json={
        "email": "user1@example.com",
        "username": "sameusername",
        "password": "TestPass123!"
    })
    response = client.post("/auth/register", json={
        "email": "user2@example.com",
        "username": "sameusername",
        "password": "TestPass123!"
    })
    
    assert response.status_code == 400
    assert "username ya existe" in response.json()["detail"].lower()

def test_register_weak_password(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "weak"
    })

    assert response.status_code == 422
    assert "detail" in response.json()

def test_login_success(client):
    client.post("/auth/register", json={
        "email": "login@example.com",
        "username": "loginuser",
        "password": "LoginPass123!"
    })

    response = client.post("/auth/login", data={
        "username": "loginuser",
        "password": "LoginPass123!"
    })

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_with_email(client):
    client.post("/auth/register", json={
        "email": "emaillogin@example.com",
        "username": "emailuser",
        "password": "EmailPass123!"
    })
    response = client.post("/auth/login", data={
        "username": "emaillogin@example.com",
        "password": "EmailPass123!"
    })

    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    client.post("/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "CorrectPass123!"
    })
    response = client.post("/auth/login", data={
        "username": "testuser",
        "password": "WrongPass123!"
    })

    assert response.status_code == 401
    assert "credenciales incorrectas" in response.json()["detail"].lower()

def test_login_nonexistent_user(client):
    response = client.post("/auth/login", data={
        "username": "nonexistent",
        "password": "SomePass123!"
    })

    assert response.status_code == 401

def test_get_current_user(client):
    client.post("/auth/register", json={
        "email": "current@example.com",
        "username": "currentuser",
        "password": "CurrentPass123!"
    })
    login_response = client.post("/auth/login", data={
        "username": "currentuser",
        "password": "CurrentPass123!"
    })

    token = login_response.json()["access_token"]

    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}"
    })

    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "currentuser"
    assert data["email"] == "current@example.com"

def test_get_current_user_no_token(client):
    response = client.get("/auth/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token(client):
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer invalid_token_here"
    })

    assert response.status_code == 401