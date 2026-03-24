def test_get_profile_success(user_client, user_info):
    response = user_client.get("/profile")
    assert response.status_code == 200, f"Failed to get profile: {response.json()}"
    data = response.json()
    assert data["email"] == user_info["email"], (
        "Email in profile does not match expected"
    )


def test_update_profile_info_success(user_client, user_info):
    new_first_name = f"Upd {user_info['first_name']}"
    new_last_name = f"Upd {user_info['last_name']}"
    new_phone_number = "+1234567890"

    response = user_client.patch(
        "/profile",
        json={
            "first_name": new_first_name,
            "last_name": new_last_name,
            "phone_number": new_phone_number,
        },
    )
    assert response.status_code == 200, (
        f"Failed to update profile info: {response.json()}"
    )
    data = response.json()
    assert data["full_name"] == f"{new_first_name} {new_last_name}", (
        "Full name was not updated correctly"
    )
    assert data["phone_number"] == new_phone_number, (
        "Phone number was not updated correctly"
    )


def test_update_profile_password_success(user_client, user_info):
    new_password = "NewPass123!"

    response = user_client.put(
        "/profile/password",
        json={
            "old_password": user_info["password"],
            "new_password": new_password,
        },
    )
    assert response.status_code == 200, (
        f"Failed to update profile password: {response.json()}"
    )
    assert response.json()["message"] == "Password changed successfully.", (
        "Unexpected success message for password change"
    )

    response = user_client.put(
        "/profile/password",
        json={
            "old_password": new_password,
            "new_password": user_info["password"],
        },
    )

    assert response.status_code == 200, (
        f"Failed to revert profile password: {response.json()}"
    )
    assert response.json()["message"] == "Password changed successfully.", (
        "Unexpected success message for password revert"
    )


def test_update_profile_password_failure(user_client, user_info):
    new_password = "NewPass123!"

    response = user_client.put(
        "/profile/password",
        json={
            "old_password": "bad_old_password",
            "new_password": new_password,
        },
    )
    assert response.status_code == 403, (
        f"Expected failure when using bad old password: {response.json()}"
    )
    assert response.json()["message"] == "Old password is incorrect.", (
        "Unexpected error message for bad old password"
    )
