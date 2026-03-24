def test_get_all_houses_success(admin_client):
    response = admin_client.get("/houses")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "has_next" in data
    assert len(data["items"]) >= 1


def test_get_all_houses_with_limit(admin_client):
    response = admin_client.get("/houses", params={"limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) <= 2


def test_get_all_houses_with_cursor(admin_client):
    first = admin_client.get("/houses", params={"limit": 2}).json()
    if not first["has_next"]:
        return  # not enough data to paginate

    cursor = first["next_cursor"]
    response = admin_client.get("/houses", params={"limit": 2, "next_cursor": cursor})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_get_all_houses_by_address(admin_client):
    response = admin_client.get("/houses", params={"address": "Siempre Viva"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1


def test_get_all_houses_by_address_no_match(admin_client):
    response = admin_client.get("/houses", params={"address": "Calle Inexistente XYZ"})
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["has_next"] is False


def test_get_all_houses_by_address_with_cursor(admin_client):
    first = admin_client.get(
        "/houses", params={"address": "Siempre Viva", "limit": 1}
    ).json()
    if not first["has_next"]:
        return

    cursor = first["next_cursor"]
    response = admin_client.get(
        "/houses", params={"address": "Siempre Viva", "limit": 1, "next_cursor": cursor}
    )
    assert response.status_code == 200


def test_get_house_by_id_success(admin_client):
    response = admin_client.get("/houses/SV101")
    assert response.status_code == 200
    data = response.json()
    assert data["_id"] == "SV101"


def test_get_house_by_id_not_found(admin_client):
    response = admin_client.get("/houses/NONEXISTENT999")
    assert response.status_code == 404
    assert response.json()["message"] == "House not found"


def test_create_house_with_explicit_id_success(admin_client):
    response = admin_client.post(
        "/houses",
        json={"id": "TEST_HOUSE_1", "number": 999, "street": "Test Street"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["_id"] == "TEST_HOUSE_1"

    # cleanup
    admin_client.delete("/houses/TEST_HOUSE_1")


def test_create_house_duplicate_id_raises_400(admin_client):
    # create once
    admin_client.post(
        "/houses",
        json={"id": "DUP_HOUSE", "number": 888, "street": "Dup Street"},
    )

    response = admin_client.post(
        "/houses",
        json={"id": "DUP_HOUSE", "number": 888, "street": "Dup Street"},
    )
    assert response.status_code == 400
    assert response.json()["message"] == "House with this ID already exists"

    # cleanup
    admin_client.delete("/houses/DUP_HOUSE")


def test_create_house_without_id_autogenerates(admin_client):
    response = admin_client.post(
        "/houses",
        json={"number": 777, "street": "Auto Street"},
    )
    assert response.status_code == 201
    data = response.json()
    generated_id = data["_id"]
    assert generated_id  # some id was generated

    # cleanup
    admin_client.delete(f"/houses/{generated_id}")


def test_create_house_with_extra_success(admin_client):
    response = admin_client.post(
        "/houses",
        json={
            "id": "EXTRA_HOUSE",
            "number": 111,
            "street": "Extra St",
            "extra": "Apt 2",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "Apt 2" in data["full_address"]

    # cleanup
    admin_client.delete("/houses/EXTRA_HOUSE")


def test_delete_house_success(admin_client):
    admin_client.post(
        "/houses",
        json={"id": "DELETE_ME", "number": 555, "street": "Delete St"},
    )
    response = admin_client.delete("/houses/DELETE_ME")
    assert response.status_code == 204


def test_delete_house_not_found(admin_client):
    response = admin_client.delete("/houses/NONEXISTENT999")
    assert response.status_code == 404
    assert response.json()["message"] == "House not found"


def test_houses_require_admin(user_client):
    response = user_client.get("/houses")
    assert response.status_code == 403
