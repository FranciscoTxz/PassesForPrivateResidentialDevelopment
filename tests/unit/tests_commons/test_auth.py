import datetime
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

import commons.auth as auth_module
from schemas.users_schema import UserInfo

SECRET = "SuperSecretKeyForTesting@!$%^&*123123"


def make_token(payload: dict) -> str:
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make_user_info(**overrides) -> UserInfo:
    data: dict[str, str | bool | None] = {
        "email": "user@example.com",
        "full_name": "Test User",
        "enabled": True,
        "house_id": "house123",
        "role": "owner",
    }
    data.update(overrides)
    return UserInfo(**data)  # ty:ignore


# ─── get_current_user_info ───────────────────────────────────────────────────


class TestGetCurrentUserInfo:
    def test_valid_token_returns_user_info(self, monkeypatch):
        user = make_user_info()
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        result = auth_module.get_current_user_info()(authorization=token)

        assert result == user

    def test_disabled_user_raises_403(self, monkeypatch):
        user = make_user_info(enabled=False)
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization=token)

        assert exc_info.value.status_code == 403
        assert "disabled" in exc_info.value.detail

    def test_missing_email_in_token_raises_401(self, monkeypatch):
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: make_user_info()
        )
        token = make_token({"sub": "no_email_here"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization=token)

        assert exc_info.value.status_code == 401

    def test_validate_owner_without_house_raises_403(self, monkeypatch):
        user = make_user_info(house_id=None)
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info(validate_owner=True)(authorization=token)

        assert exc_info.value.status_code == 403
        assert "house" in exc_info.value.detail.lower()

    def test_validate_owner_with_house_passes(self, monkeypatch):
        user = make_user_info(house_id="house123")
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        result = auth_module.get_current_user_info(validate_owner=True)(
            authorization=token
        )

        assert result == user

    def test_validate_admin_without_admin_role_raises_403(self, monkeypatch):
        user = make_user_info(role="owner")
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info(validate_admin=True)(authorization=token)

        assert exc_info.value.status_code == 403
        assert "role" in exc_info.value.detail.lower()

    def test_validate_admin_with_admin_role_passes(self, monkeypatch):
        user = make_user_info(role="admin")
        monkeypatch.setattr(
            auth_module.UserService, "get_user_info", lambda email: user
        )
        token = make_token({"email": "user@example.com"})

        result = auth_module.get_current_user_info(validate_admin=True)(
            authorization=token
        )

        assert result == user

    def test_expired_token_raises_401(self):
        token = make_token(
            {"email": "user@example.com", "exp": datetime.datetime(2000, 1, 1)}
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization=token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization="not.a.valid.token")

        assert exc_info.value.status_code == 401

    def test_none_authorization_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization=None)

        assert exc_info.value.status_code == 401

    def test_get_user_info_raises_generic_exception_returns_401(self, monkeypatch):
        monkeypatch.setattr(
            auth_module.UserService,
            "get_user_info",
            MagicMock(side_effect=RuntimeError("db error")),
        )
        token = make_token({"email": "user@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.get_current_user_info()(authorization=token)

        assert exc_info.value.status_code == 401


# ─── validate_gatehouse_token ────────────────────────────────────────────────


class TestValidateGatehouseToken:
    def test_valid_gatehouse_token_passes(self, monkeypatch):
        mock_users = MagicMock()
        monkeypatch.setattr(auth_module, "Users", mock_users)
        token = make_token({"role": "gatehouse", "admin_email": "admin@example.com"})

        auth_module.validate_gatehouse_token()(authorization=token)

        mock_users.objects.get.assert_called_once_with(email="admin@example.com")

    def test_wrong_role_raises_403(self, monkeypatch):
        monkeypatch.setattr(auth_module, "Users", MagicMock())
        token = make_token({"role": "owner", "admin_email": "admin@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization=token)

        assert exc_info.value.status_code == 403
        assert "role" in exc_info.value.detail.lower()

    def test_admin_not_found_raises_404(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(auth_module, "Users", mock_users)
        token = make_token({"role": "gatehouse", "admin_email": "ghost@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization=token)

        assert exc_info.value.status_code == 404

    def test_expired_token_raises_401(self):
        token = make_token(
            {
                "role": "gatehouse",
                "admin_email": "admin@example.com",
                "exp": datetime.datetime(2000, 1, 1),
            }
        )

        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization=token)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization="invalid.token.here")

        assert exc_info.value.status_code == 401

    def test_none_authorization_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization=None)

        assert exc_info.value.status_code == 401

    def test_generic_exception_raises_401(self, monkeypatch):
        mock_users = MagicMock()
        mock_users.objects.get.side_effect = RuntimeError("unexpected")
        monkeypatch.setattr(auth_module, "Users", mock_users)
        token = make_token({"role": "gatehouse", "admin_email": "admin@example.com"})

        with pytest.raises(HTTPException) as exc_info:
            auth_module.validate_gatehouse_token()(authorization=token)

        assert exc_info.value.status_code == 401
