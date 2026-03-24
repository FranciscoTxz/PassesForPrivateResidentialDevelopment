import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

import services.passes_service as passes_service_module
from services.passes_service import PassesService, update_passes_status

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_pass(**overrides):
    p = MagicMock()
    p.id = "pass-uuid-1"
    p.enabled = True
    p.status = "approved"
    p.pass_type = "temporary"
    p.guest_name = "John Guest"
    p.valid_from = datetime(2026, 3, 24, 10, 0)
    p.valid_until = datetime(2026, 3, 24, 15, 0)
    p.house_id = "house123"
    p.reason = None
    p.to_mongo.return_value = {
        "_id": p.id,
        "house_id": p.house_id,
        "enabled": p.enabled,
    }
    for k, v in overrides.items():
        setattr(p, k, v)
    return p


# ─── create_simple_pass ───────────────────────────────────────────────────────


class TestCreateSimplePass:
    def test_creates_pass_and_returns_message(self, monkeypatch):
        new_pass = make_mock_pass()
        mock_passes = MagicMock()
        mock_passes.return_value = new_pass
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        valid_from = datetime(2026, 3, 24, 10, 0)
        result = PassesService.create_simple_pass(
            pass_type="temporary",
            guest_name="John",
            valid_from=valid_from,
            house_id="house123",
        )

        new_pass.save.assert_called_once()
        assert result["message"] == "Pass created successfully"
        assert "pass" in result

    def test_valid_until_uses_type_hours(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.return_value = make_mock_pass()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        valid_from = datetime(2026, 3, 24, 10, 0)
        PassesService.create_simple_pass(
            "temporary_party", "Jane", valid_from, "house123"
        )

        _, kwargs = mock_passes.call_args
        assert kwargs["valid_until"] == valid_from + timedelta(hours=6)

    def test_unknown_type_defaults_to_1_hour(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.return_value = make_mock_pass()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        valid_from = datetime(2026, 3, 24, 10, 0)
        PassesService.create_simple_pass("unknown_type", "Jane", valid_from, "house123")

        _, kwargs = mock_passes.call_args
        assert kwargs["valid_until"] == valid_from + timedelta(hours=1)


# ─── create_pass_for_days ─────────────────────────────────────────────────────


class TestCreatePassForDays:
    def test_creates_pending_pass(self, monkeypatch):
        new_pass = make_mock_pass(id="pass-days-1", status="pending", enabled=False)
        mock_passes = MagicMock()
        mock_passes.return_value = new_pass
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        valid_from = datetime(2026, 3, 24, 10, 0)
        result = PassesService.create_pass_for_days(
            days=3,
            guest_name="Jane",
            valid_from=valid_from,
            reason="Maintenance",
            house_id="house123",
        )

        new_pass.save.assert_called_once()
        assert "pending approval" in result["message"]
        assert result["pass_id"] == new_pass.id

    def test_valid_until_is_days_from_valid_from(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.return_value = make_mock_pass()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        valid_from = datetime(2026, 3, 24, 10, 0)
        PassesService.create_pass_for_days(5, "Jane", valid_from, "reason", "house123")

        _, kwargs = mock_passes.call_args
        assert kwargs["valid_until"] == valid_from + timedelta(days=5)


# ─── get_passes_for_user ──────────────────────────────────────────────────────


class TestGetPassesForUser:
    def test_returns_passes(self, monkeypatch):
        passes = [make_mock_pass(), make_mock_pass(id="pass-2")]
        mock_passes = MagicMock()
        mock_passes.objects.return_value = passes
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_passes_for_user("house123")

        assert len(result["passes"]) == 2

    def test_no_passes_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.return_value = []
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.get_passes_for_user("house123")

        assert exc_info.value.status_code == 404


# ─── get_pass_qr ──────────────────────────────────────────────────────────────


class TestGetPassQr:
    def test_returns_qr_for_enabled_pass(self, monkeypatch):
        pass_obj = make_mock_pass(enabled=True)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)
        monkeypatch.setattr(
            passes_service_module, "generate_qr_base64", lambda pid: "base64data"
        )

        result = PassesService.get_pass_qr("pass-uuid-1", "house123")

        assert result == {"qr_jpg_code_base64": "base64data"}

    def test_disabled_pass_raises_400(self, monkeypatch):
        pass_obj = make_mock_pass(enabled=False)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.get_pass_qr("pass-uuid-1", "house123")

        assert exc_info.value.status_code == 400

    def test_not_found_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.get_pass_qr("nonexistent", "house123")

        assert exc_info.value.status_code == 404


# ─── get_all_passes ───────────────────────────────────────────────────────────


class TestGetAllPasses:
    def test_returns_passes_no_next(self, monkeypatch):
        passes = [make_mock_pass(id=f"p{i}") for i in range(2)]
        mock_passes = MagicMock()
        mock_passes.objects.return_value.order_by.return_value.limit.return_value = (
            passes
        )
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_all_passes(limit=15)

        assert len(result["passes"]) == 2
        assert result["has_next"] is False
        assert result["next_cursor"] is None

    def test_returns_empty_list(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.return_value.order_by.return_value.limit.return_value = []
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_all_passes()

        assert result == {"passes": [], "next_cursor": None, "has_next": False}

    def test_has_next_when_more_than_limit(self, monkeypatch):
        passes = [make_mock_pass(id=f"p{i}") for i in range(3)]
        for p in passes:
            p.to_mongo.return_value = {"_id": p.id}
        mock_passes = MagicMock()
        mock_passes.objects.return_value.order_by.return_value.limit.return_value = (
            passes
        )
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_all_passes(limit=2)

        assert result["has_next"] is True
        assert result["next_cursor"] == "p1"
        assert len(result["passes"]) == 2

    def test_uses_cursor_id(self, monkeypatch):
        passes = [make_mock_pass()]
        mock_passes = MagicMock()
        mock_passes.objects.return_value.order_by.return_value.limit.return_value = (
            passes
        )
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_all_passes(cursor_id="p0", limit=15)

        assert len(result["passes"]) == 1


# ─── search_pass_by_id ────────────────────────────────────────────────────────


class TestSearchPassById:
    def test_returns_pass(self, monkeypatch):
        pass_obj = make_mock_pass()
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.search_pass_by_id("pass-uuid-1")

        assert result == pass_obj.to_mongo()

    def test_not_found_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.search_pass_by_id("nonexistent")

        assert exc_info.value.status_code == 404


# ─── count_pending_passes ─────────────────────────────────────────────────────


class TestCountPendingPasses:
    def test_returns_count(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.return_value.count.return_value = 3
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.count_pending_passes()

        assert result == {"pending_passes": 3}


# ─── get_pending_passes ───────────────────────────────────────────────────────


class TestGetPendingPasses:
    def test_returns_pending_passes(self, monkeypatch):
        passes = [
            make_mock_pass(status="pending"),
            make_mock_pass(id="p2", status="pending"),
        ]
        mock_passes = MagicMock()
        mock_passes.objects.return_value = passes
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.get_pending_passes()

        assert len(result) == 2

    def test_no_pending_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.return_value = []
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.get_pending_passes()

        assert exc_info.value.status_code == 404


# ─── approve_pass ─────────────────────────────────────────────────────────────


class TestApprovePass:
    def test_approves_pending_pass(self, monkeypatch):
        pass_obj = make_mock_pass(status="pending", enabled=False)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.approve_pass("pass-uuid-1")

        assert pass_obj.enabled is True
        assert pass_obj.status == "approved"
        pass_obj.save.assert_called_once()
        assert result == {"message": "Pass approved successfully"}

    def test_non_pending_pass_raises_400(self, monkeypatch):
        pass_obj = make_mock_pass(status="approved")
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.approve_pass("pass-uuid-1")

        assert exc_info.value.status_code == 400

    def test_not_found_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.approve_pass("nonexistent")

        assert exc_info.value.status_code == 404


# ─── reject_pass ──────────────────────────────────────────────────────────────


class TestRejectPass:
    def test_rejects_pass(self, monkeypatch):
        pass_obj = make_mock_pass(status="pending", enabled=True)
        mock_passes = MagicMock()
        mock_passes.objects.get.return_value = pass_obj
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        result = PassesService.reject_pass("pass-uuid-1")

        assert pass_obj.enabled is False
        assert pass_obj.status == "rejected"
        pass_obj.save.assert_called_once()
        assert result == {"message": "Pass rejected successfully"}

    def test_not_found_raises_404(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        with pytest.raises(HTTPException) as exc_info:
            PassesService.reject_pass("nonexistent")

        assert exc_info.value.status_code == 404


# ─── update_passes_status ─────────────────────────────────────────────────────


class TestUpdatePassesStatus:
    def test_updates_expired_passes_and_stops(self, monkeypatch):
        mock_passes = MagicMock()
        mock_passes.objects.return_value.update = MagicMock()
        monkeypatch.setattr(passes_service_module, "Passes", mock_passes)

        sleep_call_count = 0

        async def fake_sleep(seconds):
            nonlocal sleep_call_count
            sleep_call_count += 1
            if sleep_call_count >= 1:
                raise asyncio.CancelledError()

        monkeypatch.setattr(asyncio, "sleep", fake_sleep)

        with pytest.raises(asyncio.CancelledError):
            asyncio.run(update_passes_status())

        mock_passes.objects.return_value.update.assert_called_once_with(
            enabled=False, status="expired"
        )
