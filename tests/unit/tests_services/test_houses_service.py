from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from mongoengine import DoesNotExist

import services.houses_service as houses_service_module
from services.houses_service import HouseService

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_house(id="MS1", number=1, street="Main St", full_address="Main St 1"):
    house = MagicMock()
    house.id = id
    house.number = number
    house.street = street
    house.full_address = full_address
    house.to_mongo.return_value = {
        "id": id,
        "number": number,
        "street": street,
        "full_address": full_address,
    }
    return house


# ─── _index_to_alpha_suffix ───────────────────────────────────────────────────


class TestIndexToAlphaSuffix:
    def test_zero_returns_empty(self):
        assert HouseService._index_to_alpha_suffix(0) == ""

    def test_one_returns_A(self):
        assert HouseService._index_to_alpha_suffix(1) == "A"

    def test_26_returns_Z(self):
        assert HouseService._index_to_alpha_suffix(26) == "Z"

    def test_27_returns_AA(self):
        assert HouseService._index_to_alpha_suffix(27) == "AA"

    def test_53_returns_BA(self):
        assert HouseService._index_to_alpha_suffix(53) == "BA"


# ─── get_all_houses ───────────────────────────────────────────────────────────


class TestGetAllHouses:
    def test_returns_items_no_next(self, monkeypatch):
        houses = [make_mock_house(id=f"H{i}") for i in range(2)]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.get_all_houses(limit=15)

        assert len(result["items"]) == 2
        assert result["has_next"] is False
        assert result["next_cursor"] is None

    def test_returns_empty_when_no_houses(self, monkeypatch):
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = []
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.get_all_houses()

        assert result == {"items": [], "next_cursor": None, "has_next": False}

    def test_has_next_when_more_than_limit(self, monkeypatch):
        houses = [make_mock_house(id=f"H{i}") for i in range(3)]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.get_all_houses(limit=2)

        assert result["has_next"] is True
        assert result["next_cursor"] == "H1"
        assert len(result["items"]) == 2

    def test_uses_cursor_id(self, monkeypatch):
        houses = [make_mock_house()]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.get_all_houses(cursor_id="H0", limit=15)

        assert len(result["items"]) == 1


# ─── search_houses_by_address ─────────────────────────────────────────────────


class TestSearchHousesByAddress:
    def test_returns_matching_items(self, monkeypatch):
        houses = [make_mock_house()]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.search_houses_by_address("Main")

        assert len(result["items"]) == 1
        assert result["has_next"] is False

    def test_returns_empty_when_no_match(self, monkeypatch):
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = []
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.search_houses_by_address("Nowhere")

        assert result == {"items": [], "next_cursor": None, "has_next": False}

    def test_has_next_and_cursor(self, monkeypatch):
        houses = [make_mock_house(id=f"H{i}") for i in range(3)]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.search_houses_by_address("Main", limit=2)

        assert result["has_next"] is True
        assert result["next_cursor"] == "H1"
        assert len(result["items"]) == 2

    def test_uses_cursor_id(self, monkeypatch):
        houses = [make_mock_house()]
        mock_houses = MagicMock()
        mock_houses.objects.return_value.order_by.return_value.limit.return_value = (
            houses
        )
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.search_houses_by_address("Main", cursor_id="H0")

        assert len(result["items"]) == 1


# ─── get_house_by_id ──────────────────────────────────────────────────────────


class TestGetHouseById:
    def test_returns_house_mongo_dict(self, monkeypatch):
        house = make_mock_house()
        mock_houses = MagicMock()
        mock_houses.objects.get.return_value = house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.get_house_by_id("MS1")

        assert result["id"] == "MS1"

    def test_not_found_raises_404(self, monkeypatch):
        mock_houses = MagicMock()
        mock_houses.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            HouseService.get_house_by_id("NOPE")

        assert exc_info.value.status_code == 404


# ─── create_house ─────────────────────────────────────────────────────────────


class TestCreateHouse:
    def test_create_with_explicit_id(self, monkeypatch):
        new_house = make_mock_house(id="MS1")
        mock_houses = MagicMock()
        mock_houses.objects.return_value.first.return_value = None
        mock_houses.return_value = new_house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.create_house(
            id="MS1", number=1, street="Main St", extra=None
        )

        new_house.save.assert_called_once()
        assert result["id"] == "MS1"

    def test_create_with_explicit_id_already_exists_raises_400(self, monkeypatch):
        mock_houses = MagicMock()
        mock_houses.objects.return_value.first.return_value = make_mock_house()
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            HouseService.create_house(id="MS1", number=1, street="Main St", extra=None)

        assert exc_info.value.status_code == 400

    def test_create_without_id_autogenerates(self, monkeypatch):
        new_house = make_mock_house(id="MS1")
        mock_houses = MagicMock()
        mock_houses.objects.return_value.first.return_value = None
        mock_houses.return_value = new_house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        result = HouseService.create_house(
            id=None, number=1, street="Main St", extra=None
        )

        new_house.save.assert_called_once()
        assert result["id"] == "MS1"

    def test_create_with_extra_appended_to_address(self, monkeypatch):
        new_house = MagicMock()
        new_house.to_mongo.return_value = {"full_address": "Main St 1, Apt 2"}
        mock_houses = MagicMock()
        mock_houses.objects.return_value.first.return_value = None
        mock_houses.return_value = new_house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        HouseService.create_house(id=None, number=1, street="Main St", extra="Apt 2")

        _, kwargs = mock_houses.call_args
        assert "Apt 2" in kwargs["full_address"]

    def test_create_appends_suffix_on_id_collision(self, monkeypatch):
        existing_house = make_mock_house(id="MS1")
        new_house = make_mock_house(id="MS1A")
        mock_houses = MagicMock()
        # first call: no collision for auto-generated "MS1"? No — first call in while loop finds collision,
        # second call (with "MS1A") finds none
        mock_houses.objects.return_value.first.side_effect = [existing_house, None]
        mock_houses.return_value = new_house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        HouseService.create_house(id=None, number=1, street="Main St", extra=None)

        _, kwargs = mock_houses.call_args
        assert kwargs["id"] == "MS1A"


# ─── delete_house_by_id ───────────────────────────────────────────────────────


class TestDeleteHouseById:
    def test_deletes_house(self, monkeypatch):
        house = make_mock_house()
        mock_houses = MagicMock()
        mock_houses.objects.get.return_value = house
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        HouseService.delete_house_by_id("MS1")

        house.delete.assert_called_once()

    def test_not_found_raises_404(self, monkeypatch):
        mock_houses = MagicMock()
        mock_houses.objects.get.side_effect = DoesNotExist()
        monkeypatch.setattr(houses_service_module, "Houses", mock_houses)

        with pytest.raises(HTTPException) as exc_info:
            HouseService.delete_house_by_id("NOPE")

        assert exc_info.value.status_code == 404
