"""
Authentication tests for AuthService and routes.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import AuthService
from app.models import User
from app.schemas.auth import UserRegisterRequest, UserLoginRequest


def test_auth_service_register_and_login(db_session: Session):
    auth_service = AuthService(db_session)

    # Register a new user
    user = auth_service.register_user(
        email="newuser@example.com",
        password="StrongPassw0rd!",
        full_name="New User",
    )

    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.full_name == "New User"
    assert user.password_hash != "StrongPassw0rd!"

    # Login with the registered user
    authenticated_user = auth_service.authenticate_user(
        email="newuser@example.com",
        password="StrongPassw0rd!",
    )

    assert authenticated_user is not None
    assert authenticated_user.id == user.id

    # Invalid password should fail
    invalid_auth = auth_service.authenticate_user(
        email="newuser@example.com",
        password="wrong-password",
    )

    assert invalid_auth is None


def test_register_login_routes(client: TestClient, db_session: Session):
    register_payload = {
        "email": "routeuser@example.com",
        "password": "RoutePass123!",
        "full_name": "Route User",
    }

    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "routeuser@example.com"
    assert data["user"]["full_name"] == "Route User"

    # Duplicate registration should return conflict
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 409

    # Login with correct credentials
    login_payload = {
        "email": "routeuser@example.com",
        "password": "RoutePass123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    login_data = response.json()
    assert login_data["access_token"]
    assert login_data["user"]["email"] == "routeuser@example.com"

    token = login_data["access_token"]

    # Fetch current user with token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    me_data = response.json()
    assert me_data["email"] == "routeuser@example.com"
    assert me_data["full_name"] == "Route User"

    # Invalid token should fail
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401


def test_login_route_invalid_credentials(client: TestClient):
    payload = {
        "email": "doesnotexist@example.com",
        "password": "NoSuchPassword",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"
