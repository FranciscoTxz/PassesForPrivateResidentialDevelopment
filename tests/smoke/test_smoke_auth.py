from uuid import uuid4

from fastapi.testclient import TestClient


def test_sign_up_success(dynamo_client):
    from app import app

    client = TestClient(app)

    email = f"user{uuid4()}@example.com"
    password = "TestPassword123!"

    signup_response = client.post(
        "/auth/sign-up",
        json={
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
            "phone_number": "+524492113599",
        },
    )

    assert signup_response.status_code == 201, (
        f"Sign-up failed: {signup_response.json()}"
    )


def test_sign_up_already_exists(dynamo_client, user_info):
    from app import app

    client = TestClient(app)

    password = "TestPassword123!"

    signup_response = client.post(
        "/auth/sign-up",
        json={
            "email": user_info["email"],
            "password": password,
            "first_name": "Test",
            "last_name": "User",
            "birthdate": "1990-01-01",
            "phone_number": "+524492113599",
        },
    )

    assert signup_response.status_code == 400, (
        f"Sign-up should fail for existing user: {signup_response.json()}"
    )


def test_sign_in_success(dynamo_client, user_info):
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/auth/sign-in",
        json={
            "email": user_info["email"],
            "password": user_info["password"],
        },
    )

    assert login_response.status_code == 200, f"Sign-in failed: {login_response.json()}"
    assert "access_token" in login_response.json(), (
        "No access token returned on successful sign-in"
    )


def test_sign_in_wrong_password(dynamo_client, user_info):
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/auth/sign-in",
        json={
            "email": user_info["email"],
            "password": "WrongPass123!",
        },
    )

    assert login_response.status_code == 400, (
        f"Sign-in should fail for wrong password: {login_response.json()}"
    )
    assert login_response.json()["message"] == "Invalid email or password", (
        "Unexpected error message for wrong password"
    )


def test_sign_in_user_not_found(dynamo_client):
    from app import app

    client = TestClient(app)

    login_response = client.post(
        "/auth/sign-in",
        json={
            "email": "nonexistent@example.com",
            "password": "WrongPass123!",
        },
    )

    assert login_response.status_code == 400, (
        f"Sign-in should fail for nonexistent user: {login_response.json()}"
    )
    assert login_response.json()["message"] == "Invalid email or password", (
        "Unexpected error message for nonexistent user"
    )
