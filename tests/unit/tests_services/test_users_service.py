from datetime import date
from hashlib import sha1
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

import services.users_service as users_service_module
from services.users_service import UserService

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_user(**overrides):
    user = MagicMock()
    user.email = "user@example.com"
    user.first_name = "John"
    user.last_name = "Doe"
    user.full_name = "John Doe"
    user.birthdate = "1990-01-01"
    user.phone_number = "+12345678901"
    user.password_hash = sha1(b"Password1!user@example.com").hexdigest()
    user.enabled = True
    user.house_id = None
    user.role = "user"
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def make_mock_user_with_house(**overrides):
    user = MagicMock()
    user.email = "user2@example.com"
    user.first_name = "Jean"
    user.last_name = "Paul"
    user.full_name = "Jean Paul"
    user.birthdate = "1999-10-11"
    user.phone_number = "+12345678901"
    user.password_hash = sha1(b"Password1!user@example.com").hexdigest()
    user.enabled = True
    user.house_id = "SV101"
    user.role = "user"
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


def make_mock_house(**overrides):
    house = MagicMock()
    house.id = "house123"
    house.number = 1
    house.street = "Main St"
    house.full_address = "1 Main St"
    for k, v in overrides.items():
        setattr(house, k, v)
    return house


# ─── signup_user ──────────────────────────────────────────────────────────────


class TestSignupUser:
    def test_signup_success(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.signup_user(
            first_name="John",
            last_name="Doe",
            email="new@example.com",
            password="Password1!",
            birthdate=date(1990, 1, 1),
            phone_number="+12345678901",
        )

        assert result == {"message": "User registered successfully."}
        mock_users.return_value.save.assert_called_once()

    def test_signup_duplicate_email_raises_400(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.return_value = make_mock_user()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.signup_user(
                first_name="John",
                last_name="Doe",
                email="user@example.com",
                password="Password1!",
                birthdate=date(1990, 1, 1),
                phone_number="+12345678901",
            )

        assert exc_info.value.status_code == 400


# ─── login_user ───────────────────────────────────────────────────────────────


class TestLoginUser:
    def test_login_success_returns_token(self, monkeypatch):
        user = make_mock_user(
            password_hash=sha1(b"Password1!user@example.com").hexdigest()
        )
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.login_user("user@example.com", "Password1!")

        assert "access_token" in result
        assert result["user_full_name"] == "John Doe"

    def test_login_wrong_password_raises_400(self, monkeypatch):
        user = make_mock_user()
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.login_user("user@example.com", "WrongPass1!")

        assert exc_info.value.status_code == 400

    def test_login_user_not_found_raises_400(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.login_user("ghost@example.com", "Password1!")

        assert exc_info.value.status_code == 400

    def test_login_disabled_user_raises_400(self, monkeypatch):
        user = make_mock_user(
            enabled=False,
            password_hash=sha1(b"Password1!user@example.com").hexdigest(),
        )
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.login_user("user@example.com", "Password1!")

        assert exc_info.value.status_code == 400


# ─── get_user_info ────────────────────────────────────────────────────────────


class TestGetUserInfo:
    def test_returns_user_info(self, monkeypatch):
        user = make_mock_user()
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info("user@example.com")

        assert result.email == "user@example.com"
        assert result.full_name == "John Doe"

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_info("ghost@example.com")

        assert exc_info.value.status_code == 404


# ─── update_profile_info ──────────────────────────────────────────────────────


class TestUpdateProfileInfo:
    def test_updates_fields_successfully(self, monkeypatch):
        user = make_mock_user()
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.update_profile_info(
            email="user@example.com",
            new_first_name="Jane",
            new_last_name=None,
            new_phone_number="+10987654321",
        )

        assert result["message"] == "Profile updated successfully."
        user.save.assert_called_once()

    def test_user_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_profile_info("ghost@example.com", "Jane", None, None)

        assert exc_info.value.status_code == 404


# ─── update_password ──────────────────────────────────────────────────────────


class TestUpdatePassword:
    def test_updates_password_successfully(self, monkeypatch):
        user = make_mock_user(
            password_hash=sha1(b"OldPass1!user@example.com").hexdigest()
        )
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        UserService.update_password("user@example.com", "OldPass1!", "NewPass1!")

        assert user.password_hash == sha1(b"NewPass1!user@example.com").hexdigest()
        user.save.assert_called_once()

    def test_wrong_old_password_raises_403(self, monkeypatch):
        user = make_mock_user(
            password_hash=sha1(b"OldPass1!user@example.com").hexdigest()
        )
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_password("user@example.com", "WrongPass1!", "NewPass1!")

        assert exc_info.value.status_code == 403

    def test_user_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.update_password("ghost@example.com", "OldPass1!", "NewPass1!")

        assert exc_info.value.status_code == 404


# ─── make_user_admin ──────────────────────────────────────────────────────────


class TestMakeUserAdmin:
    def test_promotes_user_to_admin(self, monkeypatch):
        user = make_mock_user(role="user")
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.make_user_admin("user@example.com")

        assert user.role == "admin"
        assert "promoted" in result["message"]

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.make_user_admin("ghost@example.com")

        assert exc_info.value.status_code == 404


# ─── disable_user / enable_user / delete_user ─────────────────────────────────


class TestDisableUser:
    def test_disables_user(self, monkeypatch):
        user = make_mock_user(enabled=True)
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.disable_user("user@example.com")

        assert user.enabled is False
        assert "disabled" in result["message"]

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.disable_user("ghost@example.com")

        assert exc_info.value.status_code == 404


class TestEnableUser:
    def test_enables_user(self, monkeypatch):
        user = make_mock_user(enabled=False)
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.enable_user("user@example.com")

        assert user.enabled is True
        assert "enabled" in result["message"]

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.enable_user("ghost@example.com")

        assert exc_info.value.status_code == 404


class TestDeleteUser:
    def test_deletes_user(self, monkeypatch):
        user = make_mock_user()
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.delete_user("user@example.com")

        user.delete.assert_called_once()
        assert "deleted" in result["message"]

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.delete_user("ghost@example.com")

        assert exc_info.value.status_code == 404


# ─── count_users_by_role ──────────────────────────────────────────────────────


class TestCountUsersByRole:
    def test_count_all_users(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.return_value.count.return_value = 5
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.count_users_by_role()

        assert result == 5

    def test_count_with_query(self, monkeypatch):
        mock_qs = MagicMock()
        mock_qs.count.return_value = 2
        mock_users = MagicMock()
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.count_users_by_role(query="John")

        assert result == 2

    def test_count_with_role_and_query(self, monkeypatch):
        mock_qs = MagicMock()
        mock_qs.count.return_value = 1
        mock_users = MagicMock()
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.count_users_by_role(role="admin", query="John")

        assert result == 1


# ─── get_all_staff ────────────────────────────────────────────────────────────


class TestGetAllStaff:
    def test_returns_paginated_users(self, monkeypatch):
        users = [make_mock_user(email=f"u{i}@x.com", role="user") for i in range(3)]
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = users
        mock_users = MagicMock()
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_all_staff(page=1, page_size=10)

        assert len(result["users"]) == 3
        assert result["has_next"] is False

    def test_has_next_when_more_than_page_size(self, monkeypatch):
        users = [make_mock_user(email=f"u{i}@x.com") for i in range(3)]
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = users
        mock_users = MagicMock()
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_all_staff(page=1, page_size=2)

        assert result["has_next"] is True
        assert result["next_page"] == 2
        assert len(result["users"]) == 2

    def test_no_users_raises_404(self, monkeypatch):
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = []
        mock_users = MagicMock()
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_all_staff()

        assert exc_info.value.status_code == 404


# ─── link_house ───────────────────────────────────────────────────────────────


class TestLinkHouse:
    def test_links_house_successfully(self, monkeypatch):
        user = make_mock_user(house_id=None)
        house = make_mock_house()
        mock_users = MagicMock()
        mock_users.objects.filter.return_value.first.return_value = None
        mock_users.objects.return_value.first.return_value = None
        mock_users.objects.get.return_value = user
        mock_houses = MagicMock()
        mock_houses.objects.get.return_value = house
        monkeypatch.setattr(users_service_module, "Users", mock_users)
        monkeypatch.setattr(users_service_module, "Houses", mock_houses)

        # patch the `Users.objects(house_id=house_id).first()` call
        mock_users.objects.return_value = MagicMock(first=MagicMock(return_value=None))

        result = UserService.link_house("user@example.com", "house123")

        assert "linked" in result["message"]
        assert user.house_id == house.id

    def test_house_already_linked_to_another_user_raises_400(self, monkeypatch):
        other_user = make_mock_user(email="other@example.com", house_id="house123")
        mock_users = MagicMock()
        mock_users.objects.return_value = MagicMock(
            first=MagicMock(return_value=other_user)
        )
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.link_house("user@example.com", "house123")

        assert exc_info.value.status_code == 400
        assert "another user" in exc_info.value.detail

    def test_user_already_linked_to_same_house_raises_400(self, monkeypatch):
        same_user = make_mock_user(email="user@example.com", house_id="house123")
        mock_users = MagicMock()
        mock_users.objects.return_value = MagicMock(
            first=MagicMock(return_value=same_user)
        )
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.link_house("user@example.com", "house123")

        assert exc_info.value.status_code == 400
        assert "already linked" in exc_info.value.detail

    def test_user_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.return_value = MagicMock(first=MagicMock(return_value=None))
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)
        monkeypatch.setattr(users_service_module, "Houses", MagicMock())

        with pytest.raises(HTTPException) as exc_info:
            UserService.link_house("ghost@example.com", "house123")

        assert exc_info.value.status_code == 404

    def test_house_not_found_raises_404(self, monkeypatch):
        user = make_mock_user()
        mock_users = MagicMock()
        mock_users.objects.return_value = MagicMock(first=MagicMock(return_value=None))
        mock_users.objects.get.return_value = user
        mock_houses = MagicMock()
        mock_houses.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)
        monkeypatch.setattr(users_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            UserService.link_house("user@example.com", "nonexistent_house")

        assert exc_info.value.status_code == 404


# ─── get_user_info_admin ──────────────────────────────────────────────────────


class TestGetUserInfoAdmin:
    def test_returns_mongo_dict(self, monkeypatch):
        user = make_mock_user()
        user.to_mongo.return_value = {"email": "user@example.com"}
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info_admin("user@example.com")

        assert result == {"email": "user@example.com"}

    def test_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_info_admin("ghost@example.com")

        assert exc_info.value.status_code == 404


# ─── get_user_info_by_email_name ──────────────────────────────────────────────


class TestGetUserInfoByEmailName:
    def test_email_query_returns_single_user(self, monkeypatch):
        user = make_mock_user()
        user.to_mongo.return_value = {"email": "user@example.com"}
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info_by_email_name("user@example.com")

        assert result["has_next"] is False
        assert result["next_page"] is None
        assert len(result["users"]) == 1

    def test_text_search_returns_results(self, monkeypatch):
        users = [make_mock_user(email=f"u{i}@x.com") for i in range(2)]
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = users
        mock_users = MagicMock()
        mock_users.objects.search_text.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info_by_email_name("John")

        assert len(result["users"]) == 2
        assert result["has_next"] is False

    def test_text_search_exception_falls_back_to_icontains(self, monkeypatch):
        users = [make_mock_user()]
        mock_qs = MagicMock()
        mock_qs.skip.return_value.limit.return_value = users
        mock_users = MagicMock()
        mock_users.objects.search_text.side_effect = Exception("text index missing")
        mock_users.objects.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info_by_email_name("John")

        assert len(result["users"]) == 1

    def test_no_results_raises_404(self, monkeypatch):
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = []
        mock_users = MagicMock()
        mock_users.objects.search_text.return_value = mock_qs
        mock_users.objects.return_value = MagicMock(
            skip=MagicMock(return_value=MagicMock(limit=MagicMock(return_value=[])))
        )
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_info_by_email_name("nobody")

        assert exc_info.value.status_code == 404

    def test_has_next_page(self, monkeypatch):
        users = [make_mock_user(email=f"u{i}@x.com") for i in range(3)]
        mock_qs = MagicMock()
        mock_qs.order_by.return_value.skip.return_value.limit.return_value = users
        mock_users = MagicMock()
        mock_users.objects.search_text.return_value = mock_qs
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_info_by_email_name("John", page=1, page_size=2)

        assert result["has_next"] is True
        assert result["next_page"] == 2
        assert len(result["users"]) == 2


# ─── get_user_info_by_email_name ──────────────────────────────────────────────


class TestGetUserByHouseId:
    @staticmethod
    def test_get_user_by_house_id(monkeypatch):
        user = make_mock_user_with_house()
        user.to_mongo.return_value = {"house_id": "SV101"}
        mock_users = MagicMock()
        mock_users.objects.get.return_value = user
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        result = UserService.get_user_by_house_id("SV101")

        assert len(result) == 1
        assert result["user"]["email"] == "user2@example.com"

    @staticmethod
    def test_no_results_raises_404(monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(users_service_module, "Users", mock_users)

        with pytest.raises(HTTPException) as exc_info:
            UserService.get_user_by_house_id("AAA")

        assert exc_info.value.status_code == 404
