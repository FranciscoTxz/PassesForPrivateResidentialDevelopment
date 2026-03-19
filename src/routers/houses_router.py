from fastapi import APIRouter, Depends, Query

from commons.auth import get_current_user_info
from schemas.houses_schema import CreateHouse
from schemas.users_schema import UserInfo
from services.houses_service import HouseService

router = APIRouter(prefix="/houses", tags=["Houses"])


@router.get("", status_code=200)
def get_all_houses(
    next_cursor: str | None = Query(default=None),
    limit: int = Query(default=15, ge=1),
    address: str | None = Query(default=None),
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    if address:
        return HouseService.search_houses_by_address(
            address=address, cursor_id=next_cursor, limit=limit
        )
    else:
        return HouseService.get_all_houses(cursor_id=next_cursor, limit=limit)


@router.get("/{house_id}", status_code=200)
def get_house(
    house_id: str,
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return HouseService.get_house_by_id(house_id=house_id)


@router.post("", status_code=201)
def create_house(
    house_data: CreateHouse,
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    return HouseService.create_house(
        id=house_data.id,
        number=house_data.number,
        street=house_data.street,
        extra=house_data.extra,
    )


@router.delete("/{house_id}", status_code=204)
def delete_house(
    house_id: str,
    user_info: UserInfo = Depends(get_current_user_info(validate_admin=True)),
):
    HouseService.delete_house_by_id(house_id=house_id)
