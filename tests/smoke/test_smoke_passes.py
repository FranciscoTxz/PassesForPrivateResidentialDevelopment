from datetime import UTC, datetime, timedelta


def future_datetime(minutes: int = 5) -> str:
    return (datetime.now(UTC) + timedelta(minutes=minutes)).isoformat()


# ─── POST /passes  (simple) ───────────────────────────────────────────────────


def test_create_simple_pass_success(user_client, dynamo_client):
    response = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "John Guest",
            "valid_from": future_datetime(),
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Pass created successfully"
    assert "_id" in data["pass"]


def test_create_simple_pass_party_type(user_client, dynamo_client):
    response = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary_party",
            "guest_name": "Party Guest",
            "valid_from": future_datetime(),
        },
    )
    assert response.status_code == 201


def test_create_simple_pass_gym_type(user_client, dynamo_client):
    response = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary_gym",
            "guest_name": "Gym Guest",
            "valid_from": future_datetime(),
        },
    )
    assert response.status_code == 201


def test_create_simple_pass_requires_owner(admin_client):
    # admin has no house assigned, so validate_owner should fail
    response = admin_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "Some Guest",
            "valid_from": future_datetime(),
        },
    )
    assert response.status_code == 403


# ─── POST /passes/days ────────────────────────────────────────────────────────


def test_create_pass_for_days_success(user_client, dynamo_client):
    response = user_client.post(
        "/passes/days",
        json={
            "days": 2,
            "guest_name": "Long Stay Guest",
            "valid_from": future_datetime(),
            "reason": "Visiting family for a few days",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "pass_id" in data
    assert "pending approval" in data["message"]


def test_create_pass_for_days_invalid_days(user_client, dynamo_client):
    response = user_client.post(
        "/passes/days",
        json={
            "days": 10,  # max is 7
            "guest_name": "Long Stay Guest",
            "valid_from": future_datetime(),
            "reason": "Way too many days for this endpoint",
        },
    )
    assert response.status_code == 400


# ─── GET /passes ──────────────────────────────────────────────────────────────


def test_get_passes_for_user_success(user_client, dynamo_client):
    user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "A Guest",
            "valid_from": future_datetime(),
        },
    )
    response = user_client.get("/passes")
    assert response.status_code == 200
    data = response.json()
    assert "passes" in data
    assert len(data["passes"]) >= 1


def test_get_passes_for_user_empty_raises_404(user_client, dynamo_client):
    response = user_client.get("/passes")
    assert response.status_code == 404


def test_get_passes_requires_owner(admin_client):
    response = admin_client.get("/passes")
    assert response.status_code == 403


# ─── GET /passes/{pass_id}/qr ─────────────────────────────────────────────────


def test_get_pass_qr_success(user_client, dynamo_client):
    create = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "QR Guest",
            "valid_from": future_datetime(),
        },
    )
    pass_id = create.json()["pass"]["_id"]

    response = user_client.get(f"/passes/{pass_id}/qr")
    assert response.status_code == 200
    assert "qr_jpg_code_base64" in response.json()


def test_get_pass_qr_not_found(user_client, dynamo_client):
    response = user_client.get("/passes/nonexistent-id/qr")
    assert response.status_code == 404


def test_get_pass_qr_disabled_raises_400(user_client, dynamo_client):
    create = user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Disabled QR Guest",
            "valid_from": future_datetime(),
            "reason": "Testing disabled pass QR scenario",
        },
    )
    pass_id = create.json()["pass_id"]

    response = user_client.get(f"/passes/{pass_id}/qr")
    assert response.status_code == 400
    assert response.json()["message"] == "Pass is not enabled"


# ─── GET /passes/all (admin) ──────────────────────────────────────────────────


def test_get_all_passes_empty(admin_client, dynamo_client):
    response = admin_client.get("/passes/all")
    assert response.status_code == 200
    data = response.json()
    assert data["passes"] == []
    assert data["has_next"] is False


def test_get_all_passes_success(admin_client, user_client, dynamo_client):
    user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "All Guest",
            "valid_from": future_datetime(),
        },
    )
    response = admin_client.get("/passes/all")
    assert response.status_code == 200
    data = response.json()
    assert len(data["passes"]) >= 1


def test_get_all_passes_with_limit_and_cursor(admin_client, user_client, dynamo_client):
    for i in range(3):
        user_client.post(
            "/passes",
            json={
                "pass_type": "temporary",
                "guest_name": f"Guest {i}",
                "valid_from": future_datetime(),
            },
        )

    first = admin_client.get("/passes/all", params={"limit": 2}).json()
    assert len(first["passes"]) == 2
    if first["has_next"]:
        cursor = first["next_cursor"]
        second = admin_client.get(
            "/passes/all", params={"limit": 2, "next_cursor": cursor}
        ).json()
        assert "passes" in second


def test_get_all_passes_requires_admin(user_client):
    response = user_client.get("/passes/all")
    assert response.status_code == 403


# ─── GET /passes/search (admin) ───────────────────────────────────────────────


def test_search_pass_by_id_success(admin_client, user_client, dynamo_client):
    create = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "Search Guest",
            "valid_from": future_datetime(),
        },
    )
    pass_id = create.json()["pass"]["_id"]

    response = admin_client.get("/passes/search", params={"pass_id": pass_id})
    assert response.status_code == 200
    assert response.json()["_id"] == pass_id


def test_search_pass_by_id_not_found(admin_client, dynamo_client):
    response = admin_client.get("/passes/search", params={"pass_id": "nonexistent-id"})
    assert response.status_code == 404


# ─── GET /passes/pending/count (admin) ────────────────────────────────────────


def test_count_pending_passes(admin_client, user_client, dynamo_client):
    user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Pending Count Guest",
            "valid_from": future_datetime(),
            "reason": "Testing pending pass count endpoint",
        },
    )
    response = admin_client.get("/passes/pending/count")
    assert response.status_code == 200
    data = response.json()
    assert "pending_passes" in data
    assert data["pending_passes"] >= 1


def test_count_pending_passes_empty(admin_client, dynamo_client):
    response = admin_client.get("/passes/pending/count")
    assert response.status_code == 200
    assert response.json()["pending_passes"] == 0


# ─── GET /passes/pending (admin) ──────────────────────────────────────────────


def test_get_pending_passes_success(admin_client, user_client, dynamo_client):
    user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Pending Guest",
            "valid_from": future_datetime(),
            "reason": "Testing get pending passes endpoint",
        },
    )
    response = admin_client.get("/passes/pending")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_pending_passes_empty_raises_404(admin_client, dynamo_client):
    response = admin_client.get("/passes/pending")
    assert response.status_code == 404


# ─── POST /passes/{pass_id}/approve (admin) ───────────────────────────────────


def test_approve_pass_success(admin_client, user_client, dynamo_client):
    create = user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Approval Guest",
            "valid_from": future_datetime(),
            "reason": "Testing pass approval flow end to end",
        },
    )
    pass_id = create.json()["pass_id"]

    response = admin_client.post(f"/passes/{pass_id}/approve")
    assert response.status_code == 200
    assert response.json()["message"] == "Pass approved successfully"


def test_approve_pass_not_pending_raises_400(admin_client, user_client, dynamo_client):
    create = user_client.post(
        "/passes",
        json={
            "pass_type": "temporary",
            "guest_name": "Already Approved",
            "valid_from": future_datetime(),
        },
    )
    pass_id = create.json()["pass"]["_id"]

    response = admin_client.post(f"/passes/{pass_id}/approve")
    assert response.status_code == 400
    assert "Only pending" in response.json()["message"]


def test_approve_pass_not_found(admin_client, dynamo_client):
    response = admin_client.post("/passes/nonexistent-id/approve")
    assert response.status_code == 404


# ─── DELETE /passes/{pass_id}/reject (admin) ──────────────────────────────────


def test_reject_pass_success(admin_client, user_client, dynamo_client):
    create = user_client.post(
        "/passes/days",
        json={
            "days": 1,
            "guest_name": "Rejected Guest",
            "valid_from": future_datetime(),
            "reason": "Testing pass rejection flow end to end",
        },
    )
    pass_id = create.json()["pass_id"]

    response = admin_client.delete(f"/passes/{pass_id}/reject")
    assert response.status_code == 200
    assert response.json()["message"] == "Pass rejected successfully"


def test_reject_pass_not_found(admin_client, dynamo_client):
    response = admin_client.delete("/passes/nonexistent-id/reject")
    assert response.status_code == 404
