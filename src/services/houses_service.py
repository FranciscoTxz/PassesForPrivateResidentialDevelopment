from fastapi import HTTPException
from mongoengine import DoesNotExist, Q

from models.houses import Houses


class HouseService:
    @staticmethod
    def _index_to_alpha_suffix(index: int) -> str:
        suffix = ""
        while index > 0:
            index, remainder = divmod(index - 1, 26)
            suffix = chr(ord("A") + remainder) + suffix
        return suffix

    @staticmethod
    def get_all_houses(cursor_id: str | None = None, limit: int = 15):
        query = Q()

        if cursor_id:
            query &= Q(id__gt=cursor_id)

        items = list(Houses.objects(query).order_by("id").limit(limit + 1))

        if not items:
            return {
                "items": [],
                "next_cursor": None,
                "has_next": False,
            }

        has_next = len(items) > limit
        page_items = items[:limit]
        next_cursor = page_items[-1].id if has_next and page_items else None

        items = [item.to_mongo() for item in page_items]

        return {
            "items": items,
            "next_cursor": str(next_cursor) if next_cursor else None,
            "has_next": has_next,
        }

    @staticmethod
    def search_houses_by_address(
        address: str, cursor_id: str | None = None, limit: int = 15
    ):
        query = Q(full_address__icontains=address)

        if cursor_id:
            query &= Q(id__gt=cursor_id)

        items = list(Houses.objects(query).order_by("id").limit(limit + 1))

        if not items:
            return {
                "items": [],
                "next_cursor": None,
                "has_next": False,
            }

        has_next = len(items) > limit
        page_items = items[:limit]
        next_cursor = page_items[-1].id if has_next and page_items else None

        items = [item.to_mongo() for item in page_items]

        return {
            "items": items,
            "next_cursor": str(next_cursor) if next_cursor else None,
            "has_next": has_next,
        }

    @staticmethod
    def get_house_by_id(house_id: str):
        try:
            return Houses.objects.get(id=house_id).to_mongo()
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="House not found")

    @staticmethod
    def create_house(id: str | None, number: int, street: str, extra: str | None):
        if id:
            if Houses.objects(id=id).first() is not None:
                raise HTTPException(
                    status_code=400, detail="House with this ID already exists"
                )

        if not id:
            street_initials = "".join([word[0] for word in street.split()])
            id = f"{street_initials.upper()}{number}"

        base_id = id
        suffix_index = 0
        while Houses.objects(id=id).first() is not None:
            suffix_index += 1
            id = f"{base_id}{HouseService._index_to_alpha_suffix(suffix_index)}"

        full_address = f"{street} {number}"
        if extra:
            full_address = f"{full_address}, {extra}"

        new_house = Houses(
            id=id, number=number, street=street, full_address=full_address
        )
        new_house.save()
        return new_house.to_mongo()

    @staticmethod
    def delete_house_by_id(house_id: str):
        try:
            house = Houses.objects.get(id=house_id)
            house.delete()
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="House not found")
