import pytest


@pytest.fixture(scope="function")
def gatehouse_token(admin_client):
    response = admin_client.post("/gatehouse/token")
    assert response.status_code == 200
    return response.json()["gatehouse_token"]


@pytest.fixture(scope="function")
def gatehouse_client(admin_client, gatehouse_token):
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)
    client.headers.update({"authorization": gatehouse_token})
    return client


# ─── /gatehouse/token ─────────────────────────────────────────────────────────


def test_get_gatehouse_token_success(admin_client):
    response = admin_client.post("/gatehouse/token")
    assert response.status_code == 200
    data = response.json()
    assert "gatehouse_token" in data
    assert "expires_in" in data


def test_get_gatehouse_token_requires_admin(user_client):
    response = user_client.post("/gatehouse/token")
    assert response.status_code == 403


# ─── /gatehouse/validate_pass ─────────────────────────────────────────────────


def test_validate_pass_not_found(gatehouse_client):
    response = gatehouse_client.get("/gatehouse/validate_pass/nonexistent-pass-id")
    assert response.status_code == 404
    assert response.json()["message"] == "Pass not found"


def test_validate_pass_success(gatehouse_client, user_client, dynamo_client):
    from datetime import UTC, datetime, timedelta

    valid_from = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    create_response = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "Gate Guest",
            "valid_from": valid_from,
        },
    )
    assert create_response.status_code == 201
    pass_id = create_response.json()["pass"]["_id"]

    # Patch valid_from to be in the past so gatehouse can validate
    from models.passes import Passes

    p = Passes.objects.get(id=pass_id)
    p.valid_from = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=5)
    p.save()

    response = gatehouse_client.get(f"/gatehouse/validate_pass/{pass_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Pass is valid and has been marked as used"


def test_validate_pass_disabled_raises_400(
    gatehouse_client, user_client, dynamo_client
):
    from datetime import UTC, datetime, timedelta

    valid_from = (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
    create_response = user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Disabled Guest",
            "valid_from": valid_from,
            "reason": "Testing disabled pass scenario",
        },
    )
    assert create_response.status_code == 201
    pass_id = create_response.json()["pass_id"]

    # The pass is created as pending (disabled), validate it directly
    response = gatehouse_client.get(f"/gatehouse/validate_pass/{pass_id}")
    assert response.status_code == 400
    assert response.json()["message"] == "Pass is not enabled"


def test_validate_pass_requires_gatehouse_token(user_client):
    response = user_client.get("/gatehouse/validate_pass/any-id")
    assert response.status_code == 403


def test_validate_pass_invalid_token(admin_client):
    from fastapi.testclient import TestClient

    from app import app

    client = TestClient(app)
    client.headers.update({"authorization": "invalid.token.value"})
    response = client.get("/gatehouse/validate_pass/any-id")
    assert response.status_code == 401
