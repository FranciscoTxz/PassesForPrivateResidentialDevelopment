from fastapi.testclient import TestClient
from pytest import fixture


@fixture(scope="function")
def user_temp_signup_login(admin_client):
    from app import app

    client = TestClient(app)

    email = "user_2@hotmail.com"
    password = "User2Pass123!"

    response_signup = client.post(
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

    assert response_signup.status_code == 201

    response_login = client.post(
        "/auth/sign-in", json={"email": email, "password": password}
    )

    assert response_login.status_code == 200

    response_login_json = response_login.json()
    token = response_login_json.get("access_token")

    client.headers.update({"authorization": token})

    yield client, email, token

    response_delete = admin_client.delete("/users/delete", params={"email": email})
    assert response_delete.status_code == 204


def test_get_users_pages_success(admin_client):
    response = admin_client.get("/users/pages", params={"page_size": 10})
    assert response.status_code == 200
    data = response.json()
    assert "total_pages" in data
    assert "total_users" in data
    assert data["total_users"] >= 1


def test_get_users_pages_query_success(admin_client):
    response = admin_client.get(
        "/users/pages", params={"page_size": 10, "query": "John"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_pages" in data
    assert "total_users" in data
    assert data["total_users"] >= 1


def test_get_users_all_success(admin_client):
    response = admin_client.get("/users", params={"page": 1, "page_size": 10})
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "has_next" in data
    assert len(data["users"]) >= 1


def test_get_users_query_success(admin_client):
    response = admin_client.get(
        "/users", params={"page": 1, "page_size": 10, "query": "John"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "has_next" in data
    assert len(data["users"]) >= 1


def test_get_users_query_email_success(admin_client):
    response = admin_client.get(
        "/users", params={"page": 1, "page_size": 10, "query": "user_1@hot.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "has_next" in data
    assert len(data["users"]) >= 1


def test_get_make_user_admin_success(admin_client, user_temp_signup_login):
    _, email, _ = user_temp_signup_login
    response = admin_client.patch("/users", params={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"User {email} has been promoted to admin."


def test_get_make_user_admin_user_not_found(admin_client):
    response = admin_client.patch("/users", params={"email": "fake_email@example.com"})
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "User with email fake_email@example.com not found"


def test_disable_enable_user_success(admin_client, user_temp_signup_login):
    client, email, _ = user_temp_signup_login
    response = admin_client.patch("/users/disable", params={"email": email})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"User {email} has been disabled."

    response_login = client.get("/passes")
    assert response_login.status_code == 403
    assert response_login.json()["message"] == "Forbidden: User account is disabled"

    response_enable = admin_client.patch("/users/enable", params={"email": email})
    assert response_enable.status_code == 200

    data_enable = response_enable.json()
    assert data_enable["message"] == f"User {email} has been enabled."


def test_link_user_to_house_success(admin_client, user_temp_signup_login):
    _, email, _ = user_temp_signup_login
    response = admin_client.patch(
        "/users/link", params={"email": email, "house_id": "SV401"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == f"User {email} has been linked to house SV401."


def test_link_user_to_house_not_found_user(admin_client):
    response = admin_client.patch(
        "/users/link", params={"email": "fake_email@example.com", "house_id": "SV401"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "User with email fake_email@example.com not found"


def test_link_user_to_house_not_found_house(admin_client, user_temp_signup_login):
    _, email, _ = user_temp_signup_login
    response = admin_client.patch(
        "/users/link", params={"email": email, "house_id": "NONEXISTENT"}
    )
    assert response.status_code == 404
    data = response.json()
    assert data["message"] == "House with id NONEXISTENT not found"


def test_link_user_to_house_already_linked(admin_client, user_temp_signup_login):
    _, email, _ = user_temp_signup_login
    response = admin_client.patch(
        "/users/link", params={"email": email, "house_id": "SV101"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == "House with id SV101 is already linked to another user"


def test_link_user_to_house_already_linked_to_user(admin_client, user_info):
    email = user_info["email"]
    house_id = user_info["house_id"]
    response = admin_client.patch(
        "/users/link", params={"email": email, "house_id": house_id}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == f"User {email} is already linked to house {house_id}"
