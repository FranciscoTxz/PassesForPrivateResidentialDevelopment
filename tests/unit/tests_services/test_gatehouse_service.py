from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

import services.gatehouse_service as gatehouse_service_module
from services.gatehouse_service import GatehouseService

SECRET = "SuperSecretKeyForTesting@!$%^&*123123"


def make_mock_pass(**overrides):
    p = MagicMock()
    p.id = "pass-uuid-1"
    p.enabled = True
    p.house_id = "house123"
    p.valid_from = datetime(2026, 3, 24, 8, 0)
    p.valid_until = datetime(2026, 3, 24, 23, 59)
    p.used = False
    p.used_date = []
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


# ─── create_token_for_gatehouse ───────────────────────────────────────────────


class TestCreateTokenForGatehouse:
    def test_returns_token_and_expiry(self, monkeypatch):
        monkeypatch.setattr(gatehouse_service_module, "SECRET_KEY", SECRET)

        result = GatehouseService.create_token_for_gatehouse("admin@example.com")

        assert "gatehouse_token" in result
        assert "expires_in" in result

    def test_token_contains_correct_claims(self, monkeypatch):
        monkeypatch.setattr(gatehouse_service_module, "SECRET_KEY", SECRET)

        result = GatehouseService.create_token_for_gatehouse("admin@example.com")

        payload = jwt.decode(result["gatehouse_token"], SECRET, algorithms=["HS256"])
        assert payload["admin_email"] == "admin@example.com"
        assert payload["role"] == "gatehouse"

    def test_token_expires_in_30_days(self, monkeypatch):
        monkeypatch.setattr(gatehouse_service_module, "SECRET_KEY", SECRET)

        result = GatehouseService.create_token_for_gatehouse("admin@example.com")

        payload = jwt.decode(result["gatehouse_token"], SECRET, algorithms=["HS256"])
        exp = datetime.fromtimestamp(payload["exp"])
        assert abs((exp - datetime.now()) - timedelta(days=30)) < timedelta(seconds=5)


# ─── validate_pass ────────────────────────────────────────────────────────────


class TestValidatePass:
    def test_valid_pass_marks_as_used(self, monkeypatch):
        now = datetime(2026, 3, 24, 12, 0)
        pass_obj = make_mock_pass(
            valid_from=datetime(2026, 3, 24, 8, 0),
            valid_until=datetime(2026, 3, 24, 23, 59),
        )
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with patch("services.gatehouse_service.datetime") as mock_dt:
            mock_dt.now.return_value.replace.return_value = now
            result = GatehouseService.validate_pass("pass-uuid-1")

        assert result == {"message": "Pass is valid and has been marked as used"}
        assert pass_obj.used is True
        pass_obj.save.assert_called_once()

    def test_pass_not_found_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            GatehouseService.validate_pass("nonexistent")

        assert exc_info.value.status_code == 404
        assert "Pass" in exc_info.value.detail

    def test_house_not_found_raises_404(self, monkeypatch):
        pass_obj = make_mock_pass()
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        mock_houses.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            GatehouseService.validate_pass("pass-uuid-1")

        assert exc_info.value.status_code == 404
        assert "House" in exc_info.value.detail

    def test_disabled_pass_raises_400(self, monkeypatch):
        pass_obj = make_mock_pass(enabled=False)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            GatehouseService.validate_pass("pass-uuid-1")

        assert exc_info.value.status_code == 400
        assert "not enabled" in exc_info.value.detail

    def test_pass_not_valid_yet_raises_400(self, monkeypatch):
        now = datetime(2026, 3, 24, 7, 0)
        pass_obj = make_mock_pass(valid_from=datetime(2026, 3, 24, 10, 0))
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with patch("services.gatehouse_service.datetime") as mock_dt:
            mock_dt.now.return_value.replace.return_value = now
            with pytest.raises(HTTPException) as exc_info:
                GatehouseService.validate_pass("pass-uuid-1")

        assert exc_info.value.status_code == 400
        assert "not valid yet" in exc_info.value.detail

    def test_expired_pass_raises_400(self, monkeypatch):
        now = datetime(2026, 3, 25, 12, 0)
        pass_obj = make_mock_pass(
            valid_from=datetime(2026, 3, 24, 8, 0),
            valid_until=datetime(2026, 3, 24, 23, 59),
        )
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with patch("services.gatehouse_service.datetime") as mock_dt:
            mock_dt.now.return_value.replace.return_value = now
            with pytest.raises(HTTPException) as exc_info:
                GatehouseService.validate_pass("pass-uuid-1")

        assert exc_info.value.status_code == 400
        assert "expired" in exc_info.value.detail

    def test_pass_without_valid_from_and_until_is_valid(self, monkeypatch):
        now = datetime(2026, 3, 24, 12, 0)
        pass_obj = make_mock_pass(valid_from=None, valid_until=None)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        mock_houses = MagicMock()
        monkeypatch.setattr(gatehouse_service_module, "Passes", mock_passes)
        monkeypatch.setattr(gatehouse_service_module, "Houses", mock_houses)

        with patch("services.gatehouse_service.datetime") as mock_dt:
            mock_dt.now.return_value.replace.return_value = now
            result = GatehouseService.validate_pass("pass-uuid-1")

        assert result == {"message": "Pass is valid and has been marked as used"}
